"""U02-U04: pending accounts, single-use credentials and request limits."""

from alembic import op
import sqlalchemy as sa

revision = "0010_account_flows"
down_revision = "0009_mail_outbox"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("core_users", sa.Column("activation_pending", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table("core_account_tokens",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("core_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(16), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("expires_at", sa.BigInteger(), nullable=False),
        sa.Column("used_at", sa.BigInteger()),
        sa.CheckConstraint("purpose IN ('activate','reset')", name="ck_account_token_purpose"))
    op.create_index("ix_account_tokens_user", "core_account_tokens", ["user_id", "purpose"])
    op.create_table("core_account_limits",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.BigInteger(), nullable=False))
    # Nullable metadata; old generic jobs remain unchanged.
    op.add_column("core_mail_outbox", sa.Column("account_user_id", sa.Integer()))
    op.add_column("core_mail_outbox", sa.Column("account_token_id", sa.String(32)))


def downgrade():
    with op.batch_alter_table("core_mail_outbox") as batch:
        batch.drop_column("account_token_id")
        batch.drop_column("account_user_id")
    op.drop_table("core_account_limits")
    op.drop_table("core_account_tokens")
    with op.batch_alter_table("core_users") as batch:
        batch.drop_column("activation_pending")
