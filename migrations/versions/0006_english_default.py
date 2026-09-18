"""S02/U07: English for new accounts; preserve existing language preferences."""

from alembic import op
import sqlalchemy as sa

revision = "0006_english_default"
down_revision = "0005_user_details"
branch_labels = None
depends_on = None


def change_default(locale):
    # SQLite's batch rebuild drops core_users. Preserve sessions before the
    # existing ON DELETE CASCADE runs, then restore them in the same transaction.
    op.execute("CREATE TEMPORARY TABLE neofab2_0006_sessions AS SELECT * FROM core_sessions")
    with op.batch_alter_table("core_users") as batch:
        batch.alter_column("locale", existing_type=sa.String(2),
                           existing_nullable=False, server_default=locale)
    op.execute("INSERT INTO core_sessions SELECT * FROM neofab2_0006_sessions "
               "WHERE token_hash NOT IN (SELECT token_hash FROM core_sessions)")
    op.execute("DROP TABLE neofab2_0006_sessions")


def upgrade():
    change_default("en")


def downgrade():
    change_default("de")
