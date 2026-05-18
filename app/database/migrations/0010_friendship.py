from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    func,
)

from alembic import op

# revision identifiers, used by Alembic.
revision        = "010"
down_revision   = "009"
branch_labels   = None
depends_on      = None

def upgrade():
    t = op.create_table("friendship",

        Column("id", Integer, primary_key=True, nullable=True, default=None),
        Column("status", Boolean, nullable=False),

        Column("customer_id_1", Integer, ForeignKey("customer.id"), nullable=True, default=None),
        Column("customer_id_2", Integer, ForeignKey("customer.id"), nullable=True, default=None),

        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False, default=None),
        Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False, default=None),

        CheckConstraint("customer_id_1 < customer_id_2", name="ck_customer_id")

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
    op.drop_table("friendship")
