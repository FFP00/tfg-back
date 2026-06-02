from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)

from alembic import op

# revision identifiers, used by Alembic.
revision        = "007"
down_revision   = "006"
branch_labels   = None
depends_on      = None

def upgrade():
    t = op.create_table("title",

        Column("id",                Integer, primary_key=True, autoincrement=True, nullable=False),

        Column("name",              String, nullable=False, unique=True),
        Column("status",            Boolean, nullable=False, server_default="false"),
        Column("actual_discount",   Integer, nullable=False),
        Column("release_date",      Date, nullable=False),
        Column("release_price",     Numeric(precision=10, scale=2), nullable=False),

        Column("developer_id",      Integer, ForeignKey("developer.id"), nullable=False),
        Column("created_at",        DateTime(timezone=True), server_default=func.now(), nullable=False),
        Column("updated_at",        DateTime(timezone=True), server_default=func.now(), nullable=False),
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
    op.drop_table("title")
