from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)

from alembic import op

revision        = "016"
down_revision   = "015"
branch_labels   = None
depends_on      = None


def upgrade():
    t = op.create_table("title_transaction",

        Column("id",                Integer, primary_key=True, autoincrement=True, nullable=False),
        Column("price",             Numeric(precision=4, scale=2), nullable=False),
        Column("discount",          Integer, nullable=False),

        Column("title_id",          Integer, ForeignKey("title.id"),        nullable=False),
        Column("transaction_id",    Integer, ForeignKey("transaction.id"),  nullable=False),

        Column("created_at",        DateTime(timezone=True), server_default=func.now(), nullable=False),
        Column("updated_at",        DateTime(timezone=True), server_default=func.now(), nullable=False),

        UniqueConstraint("title_id", "transaction_id", name="uq_title_transaction"),

        CheckConstraint('discount >= 0 AND discount <= 100')
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
    op.drop_table("title_transaction")
