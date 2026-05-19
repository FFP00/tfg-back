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
revision        = "008"
down_revision   = "007"
branch_labels   = None
depends_on      = None

def upgrade():
    t = op.create_table("title",

        Column("id", Integer, primary_key=True, autoincrement=True, nullable=False),
        Column("name", String, nullable=False, unique=True),
        Column("status", Boolean, nullable=False),
        Column("actual_discount", Integer, nullable=False),
        Column("release_date", Date, nullable=False),
        Column("release_price", Numeric(precision=10, scale=2), nullable=False),

        Column("developer_id", Integer, ForeignKey("developer.id"), nullable=True, default=None),
        Column("media_id", Integer, ForeignKey("media.id"), nullable=True, default=None),
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
    op.drop_table("title")
