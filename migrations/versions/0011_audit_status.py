"""S09/S12: structured audit events and last mail worker observation."""
from alembic import op
import sqlalchemy as sa

revision = "0011_audit_status"
down_revision = "0010_account_flows"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("core_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("module_id", sa.String(80), nullable=False),
        sa.Column("event", sa.String(160), nullable=False),
        sa.Column("actor_id", sa.Integer()), sa.Column("target_id", sa.Integer()),
        sa.Column("count", sa.Integer()))
    op.create_index("ix_audit_created", "core_audit_events", ["created_at", "id"])
    op.create_table("core_worker_status",
        sa.Column("name", sa.String(40), primary_key=True),
        sa.Column("run_id", sa.String(32), nullable=False),
        sa.Column("started_at", sa.BigInteger(), nullable=False),
        sa.Column("finished_at", sa.BigInteger()),
        sa.Column("state", sa.String(16), nullable=False))


def downgrade():
    op.drop_table("core_worker_status")
    op.drop_index("ix_audit_created", table_name="core_audit_events")
    op.drop_table("core_audit_events")
