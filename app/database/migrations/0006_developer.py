from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from alembic import op

# revision identifiers, used by Alembic.
revision        = "006"
down_revision   = "005"
branch_labels   = None
depends_on      = None

def upgrade():
    t = op.create_table("developer",

        Column("id", Integer, primary_key=True, autoincrement=True, nullable=False),
        Column("name", String, nullable=False, unique=True),
        Column("email", String, nullable=False, unique=True),
        Column("support_email", String, nullable=False, unique=True),
        Column("password", String, nullable=False),
        Column("website_url", String, nullable=False),
        Column("status", Boolean, nullable=False),


        Column("image_id", Integer, ForeignKey("image.id"), nullable=True, default=None),
        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False, default=None),
        Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False, default=None),
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
    op.drop_table("developer")
