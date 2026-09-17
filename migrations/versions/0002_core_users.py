"""U01/U05/U06/U08: Benutzer, widerrufbare Sitzungen und Anmeldebegrenzung."""

from alembic import op
import sqlalchemy as sa

revision = "0002_core_users"
down_revision = "0001_core_settings"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "core_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'staff', 'admin')", name="ck_core_users_role"),
    )
    op.create_table(
        "core_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("core_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("last_seen", sa.BigInteger(), nullable=False),
    )
    op.create_index("ix_core_sessions_user", "core_sessions", ["user_id"])
    op.create_index("ix_core_sessions_last_seen", "core_sessions", ["last_seen"])
    op.create_table(
        "core_login_attempts",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.BigInteger(), nullable=False),
    )


def downgrade():
    op.drop_table("core_login_attempts")
    op.drop_table("core_sessions")
    op.drop_table("core_users")
