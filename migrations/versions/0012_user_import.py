"""U09/N04: stable user import identity and last imported target fingerprint."""
from alembic import op
import sqlalchemy as sa

revision = "0012_user_import"
down_revision = "0011_audit_status"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("core_user_imports",
        sa.Column("source", sa.String(64), primary_key=True),
        sa.Column("source_id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("core_users.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("source_digest", sa.String(64), nullable=False),
        sa.Column("target_digest", sa.String(64), nullable=False))


def downgrade():
    op.drop_table("core_user_imports")
