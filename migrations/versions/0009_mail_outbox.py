"""Persistente Versandaufträge, S06/N01."""

from alembic import op
import sqlalchemy as sa

revision = "0009_mail_outbox"
down_revision = "0008_core_files"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "core_mail_outbox",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("module_id", sa.String(80), nullable=False),
        sa.Column("dedupe_key", sa.String(120), nullable=False),
        sa.Column("recipient", sa.String(254), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("total_attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("next_attempt_at", sa.BigInteger(), nullable=False),
        sa.Column("sent_at", sa.BigInteger()),
        sa.Column("lease_until", sa.BigInteger()),
        sa.Column("lease_token", sa.String(32)),
        sa.Column("error_code", sa.String(40)),
        sa.UniqueConstraint("module_id", "dedupe_key", name="uq_mail_dedupe"),
        sa.CheckConstraint("status IN ('queued','sending','retry','sent','failed','uncertain')", name="ck_mail_status"),
    )
    op.create_index("ix_mail_pending", "core_mail_outbox", ["status", "next_attempt_at"])


def downgrade():
    op.drop_table("core_mail_outbox")
