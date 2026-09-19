"""U05/S04: empty managed lists for user attributes; no legacy data import."""

from alembic import op
import sqlalchemy as sa

revision = "0007_user_options"
down_revision = "0006_english_default"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "core_user_options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("kind", "name", name="uq_core_user_options_kind_name"),
        sa.CheckConstraint("kind IN ('position', 'study_program', 'cost_center')", name="ck_core_user_options_kind"),
    )


def downgrade():
    op.drop_table("core_user_options")
