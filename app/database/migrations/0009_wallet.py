from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, func

from alembic import op

# revision identifiers, used by Alembic.
revision        = "009"
down_revision   = "008"
branch_labels   = None
depends_on      = None

def upgrade():
    t = op.create_table("wallet",

        Column("customer_id", Integer, ForeignKey("customer.id"), primary_key=True, nullable=True, default=None),
        Column("balance", Integer, nullable=False, unique=True),

        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False, default=None),
        Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False, default=None),

        CheckConstraint("balance >= 0", name="ck_balance_positive")

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
    op.drop_table("wallet")
