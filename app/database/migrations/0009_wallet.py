from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    func,
)

from alembic import op

revision        = "009"
down_revision   = "008"
branch_labels   = None
depends_on      = None


def upgrade():
    t = op.create_table("wallet",

        Column("customer_id", Integer, ForeignKey("customer.id"), primary_key=True, nullable=False),
        Column("balance",     Numeric(precision=10, scale=2), nullable=True, default=None),

        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False, default=None),
        Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False, default=None),

        CheckConstraint("balance >= 0", name="ck_balance_positive"),
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
        CREATE OR REPLACE FUNCTION create_wallet_for_customer()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO wallet (customer_id, balance)
            VALUES (NEW.id, 0);
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        DROP TRIGGER IF EXISTS tr_customer_create_wallet ON customer;
        CREATE TRIGGER tr_customer_create_wallet
        AFTER INSERT ON customer
        FOR EACH ROW
        EXECUTE PROCEDURE create_wallet_for_customer();
    """)

def downgrade():
    op.drop_table("wallet")
