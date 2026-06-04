from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from alembic import op

revision        = "018"
down_revision   = "017"
branch_labels   = None
depends_on      = None


def upgrade():
    t= op.create_table("otp",

        Column("user_id",       Integer, ForeignKey("user.id"), primary_key=True, nullable=False),
        Column("code",          String(4), nullable=False),

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


def downgrade():
    op.drop_table("otp")
