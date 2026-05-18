from sqlalchemy import (
    Column,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    func,
)

from alembic import op

# revision identifiers, used by Alembic.
revision        = "015"
down_revision   = "014"
branch_labels   = None
depends_on      = None

def upgrade():
    t = op.create_table("title_transaction",

        Column("id", Integer, primary_key=True, nullable=True, default=None),
        Column("price", Double, nullable=False),
        Column("discount", Integer, nullable=False),

        Column("title_id", Integer, ForeignKey("title.id"), nullable=True, default=None),
        Column("transaction_id", Integer, ForeignKey("transaction.id"), nullable=True, default=None),

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
    op.drop_table("title_transaction")
