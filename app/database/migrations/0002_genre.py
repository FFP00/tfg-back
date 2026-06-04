from sqlalchemy import Column, DateTime, Integer, String, func

from alembic import op

revision        = "002"
down_revision   = "001"
branch_labels   = None
depends_on      = None


def upgrade():
    t = op.create_table("genre",

        Column("id",            Integer, primary_key=True, autoincrement=True, nullable=False),

        Column("name",          String(50), nullable=False, unique=True),

        Column("created_at",    DateTime(timezone=True), server_default=func.now(), nullable=False),
        Column("updated_at",    DateTime(timezone=True), server_default=func.now(), nullable=False),
    )

    op.execute(f"""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        DROP TRIGGER IF EXISTS tr_{t.name}_updated_at ON {t.name};
        CREATE TRIGGER tr_{t.name}_updated_at
        BEFORE UPDATE ON {t.name}
        FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
    """)


def downgrade():
    op.drop_table("genre")
