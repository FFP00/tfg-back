from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    func,
)

from alembic import op

# revision identifiers, used by Alembic.
revision        = "011"
down_revision   = "010"
branch_labels   = None
depends_on      = None

def upgrade():
    t = op.create_table("genre_title",

        Column("id", Integer, primary_key=True, nullable=True, default=None),

        Column("title_id", Integer, ForeignKey("title.id"), nullable=True, default=None),
        Column("genre_id", Integer, ForeignKey("genre.id"), nullable=True, default=None),

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
    op.drop_table("genre_title")
