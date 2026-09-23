"""S03/S08: UTC conversion and deliberately small, escaped Markdown subset."""
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from markupsafe import Markup, escape


def validate_timezone(name):
    if not isinstance(name, str) or len(name) > 100:
        raise ValueError("Choose a valid IANA time zone.")
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("Choose a valid IANA time zone.") from None
    return name


def format_datetime(value, zone="UTC"):
    """Epoch or aware datetime; naive inputs are rejected, never guessed."""
    if value is None:
        return "—"
    if not isinstance(value, datetime):
        value = datetime.fromtimestamp(value, timezone.utc)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("A timezone-aware datetime is required.")
    local = value.astimezone(ZoneInfo(validate_timezone(zone)))
    return f"{local:%Y-%m-%d %H:%M:%S %z} ({zone})"


def render_markdown(text):
    """No raw HTML, URLs, images or attributes; only generated structural tags."""
    output, paragraph, items = [], [], []

    def inline(value):
        value = str(escape(value))
        return re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", value)

    def flush():
        if paragraph:
            output.append("<p>" + "<br>".join(inline(line) for line in paragraph) + "</p>")
            paragraph.clear()
        if items:
            output.append("<ul>" + "".join("<li>" + inline(line) + "</li>" for line in items) + "</ul>")
            items.clear()

    for line in text.splitlines():
        heading = re.fullmatch(r"(#{1,6})\s+(.+)", line)
        if heading:
            flush()
            level = len(heading[1])
            output.append(f"<h{level}>" + inline(heading[2]) + f"</h{level}>")
        elif line.startswith("- "):
            if paragraph:
                flush()
            items.append(line[2:])
        elif not line.strip():
            flush()
        else:
            if items:
                flush()
            paragraph.append(line)
    flush()
    return Markup("\n".join(output))
