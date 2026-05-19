from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)

from alembic import op

# revision identifiers, used by Alembic.
revision        = "014"
down_revision   = "013"
branch_labels   = None
depends_on      = None

def upgrade():
    t = op.create_table("review",

        Column("id", Integer, primary_key=True, nullable=True, default=None),
        Column("content", String, nullable=False),
        Column("votes", Integer, nullable=False),
        Column("recommends", Boolean, nullable=False),
        Column("status", Boolean, nullable=False, default=False),

        Column("customer_title_id", Integer, ForeignKey("customer_title.id"), nullable=True, default=None),
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
    op.drop_table("review")
