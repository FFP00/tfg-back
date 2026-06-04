from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)

from alembic import op

revision        = "013"
down_revision   = "012"
branch_labels   = None
depends_on      = None


def upgrade():
    t = op.create_table("customer_title",

        Column("id",                Integer, primary_key=True, autoincrement=True, nullable=False),

        Column("title_id",          Integer, ForeignKey("title.id"),           nullable=False),
        Column("customer_user_id",  Integer, ForeignKey("customer.user_id"),   nullable=False),
        Column("playtime",          Numeric(4), nullable=False, server_default="0"),

        Column("created_at",        DateTime(timezone=True), server_default=func.now(), nullable=False),
        Column("updated_at",        DateTime(timezone=True), server_default=func.now(), nullable=False),

        UniqueConstraint("customer_user_id", "title_id", name="uq_customer_title"),
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
    op.drop_table("customer_title")
