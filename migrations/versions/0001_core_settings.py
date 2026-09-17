"""X07: leere Core-Einstellungstabelle, keine Fach- oder Benutzerdaten."""

from alembic import op
import sqlalchemy as sa

revision = "0001_core_settings"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "core_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
    )


def downgrade():
    op.drop_table("core_settings")
