"""N01/S10: transactional small files, no existing data import."""
from alembic import op
import sqlalchemy as sa

revision = "0008_core_files"
down_revision = "0007_user_options"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("core_files",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plugin_id", sa.String(80), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("core_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.CheckConstraint("size > 0 AND size <= 1048576", name="ck_core_files_size"))
    op.create_index("ix_core_files_plugin_owner", "core_files", ["plugin_id", "owner_id"])


def downgrade():
    op.drop_table("core_files")
