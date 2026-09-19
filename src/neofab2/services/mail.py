"""Persistente Outbox und begrenzter SMTP-Worker; kein Versand im Webrequest."""

import json
import re
import secrets
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.policy import SMTP

from email_validator import validate_email, EmailNotValidError
from sqlalchemy import Column, MetaData, Table, String, Text, Integer, BigInteger, select, update
from sqlalchemy.dialects.sqlite import insert

from neofab2.core.settings import settings
from neofab2.core.users import get_user, has_permission, write_transaction

DEFAULTS = dict(enabled=False, host="", port=587, mode="starttls", sender="", username="")
SETTING_KEY = "core.smtp"
MAX_ATTEMPTS = 5
LEASE_SECONDS = 300
outbox = Table("core_mail_outbox", MetaData(),
    Column("id", String(32), primary_key=True), Column("module_id", String(80)),
    Column("dedupe_key", String(120)), Column("recipient", String(254)),
    Column("subject", String(200)), Column("body", Text), Column("status", String(16)),
    Column("attempts", Integer), Column("total_attempts", Integer),
    Column("created_at", BigInteger), Column("next_attempt_at", BigInteger),
    Column("sent_at", BigInteger), Column("lease_until", BigInteger),
    Column("lease_token", String(32)), Column("error_code", String(40)))


def mailbox(value):
    try:
        return validate_email(value, check_deliverability=False, allow_smtputf8=False).ascii_email
    except (EmailNotValidError, TypeError, AttributeError):
        raise ValueError("Please enter a valid single email address.") from None


def validate_settings(values):
    if set(values) != set(DEFAULTS):
        raise ValueError("Unknown or missing SMTP setting.")
    result = dict(values)
    if type(result["enabled"]) is not bool or type(result["port"]) is not int or not 1 <= result["port"] <= 65535:
        raise ValueError("Invalid SMTP activation or port.")
    for key in ("host", "sender", "username", "mode"):
        if not isinstance(result[key], str) or len(result[key]) > 254 or any(ord(c) < 32 for c in result[key]):
            raise ValueError("Invalid SMTP setting.")
        result[key] = result[key].strip()
    if result["mode"] not in {"starttls", "ssl", "plain"}:
        raise ValueError("Please select a valid transport.")
    if result["host"] and not re.fullmatch(r"[A-Za-z0-9.:-]+", result["host"]):
        raise ValueError("Enter an SMTP host without URL, path or credentials.")
    if result["sender"]:
        result["sender"] = mailbox(result["sender"])
    if result["mode"] == "plain" and result["username"]:
        raise ValueError("SMTP authentication requires TLS.")
    if result["enabled"] and (not result["host"] or not result["sender"]):
        raise ValueError("SMTP host and sender are required to enable sending.")
    return result


def read_settings(connection):
    raw = connection.execute(select(settings.c.value).where(settings.c.key == SETTING_KEY)).scalar_one_or_none()
    if raw is None:
        return dict(DEFAULTS)
    try:
        return validate_settings(json.loads(raw))
    except (ValueError, TypeError):
        # Beschädigte Konfiguration darf keinen Versand auslösen.
        raise ValueError("Saved SMTP settings are invalid. Please save them again.") from None


def save_settings(app, actor_id, values):
    values = validate_settings(values)
    if values["enabled"] and values["username"] and not app.config["SMTP_PASSWORD"]:
        raise ValueError("SMTP_PASSWORD is missing from the protected configuration file.")
    with write_transaction(app) as connection:
        require_admin(connection, actor_id)
        statement = insert(settings).values(key=SETTING_KEY, value=json.dumps(values))
        connection.execute(statement.on_conflict_do_update(index_elements=[settings.c.key], set_={"value": statement.excluded.value}))


def require_admin(connection, actor_id):
    if not has_permission(get_user(connection, actor_id), "core.settings.manage"):
        raise PermissionError("SMTP administration requires permission.")


def enqueue(connection, module_id, dedupe_key, recipient, subject, body):
    """Trusted service API: caller owns transaction; identical submissions are idempotent."""
    if not isinstance(module_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", module_id):
        raise ValueError("Invalid mail module.")
    if not isinstance(dedupe_key, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", dedupe_key):
        raise ValueError("Invalid idempotency key.")
    recipient = mailbox(recipient)
    if not isinstance(subject, str) or not 1 <= len(subject.strip()) <= 200 or any(ord(c) < 32 for c in subject):
        raise ValueError("The subject must contain 1–200 characters without line breaks.")
    if not isinstance(body, str) or not 1 <= len(body.encode("utf-8")) <= 65536 or "\x00" in body:
        raise ValueError("The message body must contain 1–65536 bytes.")
    identity = (outbox.c.module_id == module_id) & (outbox.c.dedupe_key == dedupe_key)
    previous = connection.execute(select(outbox).where(identity)).mappings().first()
    if previous:
        if (previous["recipient"], previous["subject"], previous["body"]) != (recipient, subject, body):
            raise ValueError("The idempotency key has already been used for a different job.")
        return previous["id"]
    job_id, now = secrets.token_hex(16), int(time.time())
    connection.execute(outbox.insert().values(id=job_id, module_id=module_id, dedupe_key=dedupe_key,
        recipient=recipient, subject=subject, body=body, status="queued", attempts=0,
        total_attempts=0, created_at=now, next_attempt_at=now))
    return job_id


def active_modules(app, connection):
    from neofab2.core.plugin_state import _read
    registry = app.extensions["neofab2_plugins"]
    selected = set(_read(connection, app.config["ENABLED_PLUGINS"])[0])
    active = {"core"}
    for plugin in registry.ordered:
        if plugin.plugin_id in selected and all(dep.plugin_id in active for dep in plugin.dependencies):
            active.add(plugin.plugin_id)
    return active


def claim(app):
    now = int(time.time())
    with write_transaction(app) as connection:
        connection.execute(update(outbox).where(outbox.c.status == "sending", outbox.c.lease_until <= now).values(
            status="uncertain", error_code="worker_interrupted", lease_token=None, lease_until=None))
        config = read_settings(connection)
        if not config["enabled"]:
            return None
        job = connection.execute(select(outbox).where(
            outbox.c.status.in_(["queued", "retry"]), outbox.c.next_attempt_at <= now,
            outbox.c.module_id.in_(active_modules(app, connection)), outbox.c.attempts < MAX_ATTEMPTS
        ).order_by(outbox.c.created_at, outbox.c.id).limit(1)).mappings().first()
        if job is None:
            return None
        job = dict(job)
        job.update(status="sending", attempts=job["attempts"] + 1,
                   total_attempts=job["total_attempts"] + 1, lease_token=secrets.token_hex(16), lease_until=now + LEASE_SECONDS)
        connection.execute(update(outbox).where(outbox.c.id == job["id"]).values(**job))
        return job, config


def deliver(config, password, job):
    """Return sanitized (state, reason); never expose SMTP responses or credentials."""
    if config["username"] and not password:
        return "failed", "credentials_missing"
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = config["sender"], job["recipient"], job["subject"]
    message["Message-ID"] = f"<neofab2-{job['id']}@{config['sender'].split('@')[1]}>"
    message.set_content(job["body"], cte="quoted-printable")
    client, data_started = None, False
    try:
        if config["mode"] == "ssl":
            client = smtplib.SMTP_SSL(host=config["host"], port=config["port"], timeout=10,
                                      context=ssl.create_default_context())
        else:
            client = smtplib.SMTP(host=config["host"], port=config["port"], timeout=10)
        client.ehlo_or_helo_if_needed()
        if config["mode"] == "starttls":
            client.starttls(context=ssl.create_default_context())
            client.ehlo()
        if config["username"]:
            client.login(config["username"], password)
        code, response = client.mail(config["sender"])
        if code != 250:
            raise smtplib.SMTPSenderRefused(code, response, config["sender"])
        code, response = client.rcpt(job["recipient"])
        if code not in (250, 251):
            raise smtplib.SMTPResponseException(code, response)
        data_started = True
        code, response = client.data(message.as_bytes(policy=SMTP))
        if code != 250:
            raise smtplib.SMTPDataError(code, response)
        return "sent", None
    except smtplib.SMTPResponseException as error:
        return ("retry" if 400 <= error.smtp_code < 500 else "failed"), "smtp_rejected"
    except (OSError, smtplib.SMTPServerDisconnected):
        return ("uncertain", "delivery_unknown") if data_started else ("retry", "connection_failed")
    except smtplib.SMTPException:
        return ("uncertain" if data_started else "failed"), "smtp_protocol"
    except Exception:
        return ("uncertain" if data_started else "failed"), "transport_error"
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


def run_worker(app, limit=20):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("The worker limit must be between 1 and 100.")
    counts = dict(sent=0, retry=0, failed=0, uncertain=0)
    for _ in range(limit):
        claimed = claim(app)
        if claimed is None:
            break
        job, config = claimed
        state, reason = deliver(config, app.config["SMTP_PASSWORD"], job)
        if state == "retry" and job["attempts"] >= MAX_ATTEMPTS:
            state, reason = "failed", "attempts_exhausted"
        now = int(time.time())
        with write_transaction(app) as connection:
            result = connection.execute(update(outbox).where(outbox.c.id == job["id"],
                outbox.c.status == "sending", outbox.c.lease_token == job["lease_token"]).values(
                status=state, error_code=reason, sent_at=now if state == "sent" else None,
                next_attempt_at=now + 60 * 2 ** (job["attempts"] - 1), lease_until=None, lease_token=None))
            if result.rowcount:
                counts[state] += 1
    return counts


def retry_job(app, actor_id, job_id, acknowledge=False):
    with write_transaction(app) as connection:
        require_admin(connection, actor_id)
        job = connection.execute(select(outbox).where(outbox.c.id == job_id)).mappings().first()
        if job is None or job["status"] not in {"failed", "uncertain"}:
            raise ValueError("Only failed or uncertain jobs can be queued again.")
        if job["status"] == "uncertain" and not acknowledge:
            raise ValueError("Uncertain delivery requires acknowledgement of possible duplicate delivery.")
        connection.execute(update(outbox).where(outbox.c.id == job_id).values(status="queued", attempts=0,
            error_code=None, next_attempt_at=int(time.time())))
