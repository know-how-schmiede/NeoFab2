"""U07: persönliche Darstellung; bestehende Konten folgen der Systemvorgabe."""

from alembic import op
import sqlalchemy as sa

revision = "0003_user_theme"
down_revision = "0002_core_users"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("core_users", sa.Column("theme", sa.String(10), nullable=False, server_default="system"))


def downgrade():
    op.drop_column("core_users", "theme")
