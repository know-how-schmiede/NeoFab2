"""U05: optionale administrative Benutzerattribute; keine Bestandsdatenübernahme."""

from alembic import op
import sqlalchemy as sa

revision = "0005_user_details"
down_revision = "0004_user_locale"
branch_labels = None
depends_on = None

# Unabhängig von veränderlichen Laufzeitmodellen versioniert halten.
FIELDS = {"salutation": 50, "first_name": 100, "last_name": 100, "address": 500,
          "position": 150, "cost_center": 100, "study_program": 150, "note": 2000}


def upgrade():
    for key, length in FIELDS.items():
        op.add_column("core_users", sa.Column(key, sa.String(length), nullable=False, server_default=""))


def downgrade():
    for key in reversed(FIELDS):
        op.drop_column("core_users", key)
