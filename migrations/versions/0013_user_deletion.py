"""U05: retain import identities after an explicitly confirmed account deletion."""
from alembic import op
import sqlalchemy as sa

revision = '0013_user_deletion'
down_revision = '0012_user_import'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('core_user_imports') as batch:
        batch.alter_column('user_id', existing_type=sa.Integer(), nullable=True)


def downgrade():
    connection = op.get_bind()
    if connection.execute(sa.text('SELECT 1 FROM core_user_imports WHERE user_id IS NULL LIMIT 1')).first():
        raise RuntimeError('Deletion markers exist; restore a matching backup instead of downgrading.')
    with op.batch_alter_table('core_user_imports') as batch:
        batch.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
