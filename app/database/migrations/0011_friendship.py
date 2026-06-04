from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)

from alembic import op

revision        = "011"
down_revision   = "010"
branch_labels   = None
depends_on      = None


def upgrade():
    ENUM_TYPE = Enum("pending", "accepted", native_enum=False)

    t = op.create_table("friendship",

        Column("id",                   Integer, primary_key=True, autoincrement=True, nullable=False),

        Column("status",               ENUM_TYPE, nullable=False, server_default="pending"),

        Column("customer_user_id_1",   Integer, ForeignKey("customer.user_id"), nullable=False),
        Column("customer_user_id_2",   Integer, ForeignKey("customer.user_id"), nullable=False),
        Column("initiator_id",         Integer, ForeignKey("customer.user_id"), nullable=False),

        Column("created_at",           DateTime(timezone=True), server_default=func.now(), nullable=False),
        Column("updated_at",           DateTime(timezone=True), server_default=func.now(), nullable=False),

        CheckConstraint("customer_user_id_1 < customer_user_id_2",                                                name="ck_friendship_order"),
        CheckConstraint("initiator_id = customer_user_id_1 OR initiator_id = customer_user_id_2",              name="ck_friendship_initiator"),
        UniqueConstraint("customer_user_id_1", "customer_user_id_2",                                           name="uq_friendship_pair"),
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
