from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from alembic import op

revision        = "005"
down_revision   = "004"
branch_labels   = None
depends_on      = None


def upgrade():
    t = op.create_table("developer",

        Column("id",            Integer, primary_key=True, autoincrement=True, nullable=False),

        Column("name",          String,  nullable=False, unique=True),
        Column("email",         String,  nullable=False, unique=True),
        Column("support_email", String,  nullable=False, unique=True),
        Column("password",      String,  nullable=False),
        Column("website_url",   String,  nullable=True, unique=True),
        Column("status",        Boolean, nullable=False, server_default="false"),

        Column("image_id",      Integer, ForeignKey("image.id"), nullable=False, default=None, unique=True),
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

    op.execute("""
        CREATE OR REPLACE FUNCTION create_developer_image()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO image (created_at, updated_at) VALUES (now(), now()) RETURNING id INTO NEW.image_id;
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        DROP TRIGGER IF EXISTS tr_developer_create_image ON developer;
        CREATE TRIGGER tr_developer_create_image
        BEFORE INSERT ON developer
        FOR EACH ROW
        EXECUTE PROCEDURE create_developer_image();
    """)


def downgrade():
    op.drop_table("developer")
