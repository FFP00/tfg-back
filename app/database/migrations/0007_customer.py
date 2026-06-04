from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, func

from alembic import op

revision        = "007"
down_revision   = "006"
branch_labels   = None
depends_on      = None


def upgrade():
    t = op.create_table("customer",

        Column("user_id",       Integer, ForeignKey("user.id"), primary_key=True, nullable=False),

        Column("status",        Boolean, nullable=False, server_default="true"),

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
        CREATE OR REPLACE FUNCTION check_customer_type()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (SELECT type FROM "user" WHERE id = NEW.user_id) != 'CUS' THEN
                RAISE EXCEPTION 'user % is not of type CUS', NEW.user_id;
            END IF;
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        DROP TRIGGER IF EXISTS tr_customer_check_type ON customer;
        CREATE TRIGGER tr_customer_check_type
        BEFORE INSERT ON customer
        FOR EACH ROW
        EXECUTE PROCEDURE check_customer_type();
    """)


def downgrade():
    op.drop_table("customer")
