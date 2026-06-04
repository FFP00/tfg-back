from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, func

from alembic import op

revision        = "005"
down_revision   = "004"
branch_labels   = None
depends_on      = None


def upgrade():
    t = op.create_table("image",

        Column("user_id",       Integer, ForeignKey("user.id"), primary_key=True, nullable=False),

        Column("profile",       LargeBinary, nullable=True),
        Column("banner",        LargeBinary, nullable=True),

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
        CREATE OR REPLACE FUNCTION create_user_image()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO image (user_id, created_at, updated_at)
            VALUES (NEW.id, now(), now());
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        DROP TRIGGER IF EXISTS tr_user_create_image ON "user";
        CREATE TRIGGER tr_user_create_image
        AFTER INSERT ON "user"
        FOR EACH ROW
        EXECUTE PROCEDURE create_user_image();
    """)

def downgrade():
    op.drop_table("image")
