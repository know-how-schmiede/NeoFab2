from alembic import context

connection = context.config.attributes.get("connection")
if connection is None:
    raise RuntimeError("Migrationen über 'neofab2 migrate' ausführen.")

context.configure(connection=connection, target_metadata=None, render_as_batch=True)
with context.begin_transaction():
    context.run_migrations()
