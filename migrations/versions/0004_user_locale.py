"""S02/U07: dauerhafte Sprachwahl, bestehende Konten bleiben deutsch."""

from alembic import op
import sqlalchemy as sa

revision = "0004_user_locale"
down_revision = "0003_user_theme"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("core_users", sa.Column("locale", sa.String(2), nullable=False, server_default="de"))


def downgrade():
    op.drop_column("core_users", "locale")
