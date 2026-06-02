from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, func

from alembic import op

# revision identifiers, used by Alembic.
revision        = "008"
down_revision   = "007"
branch_labels   = None
depends_on      = None

def upgrade():
    t = op.create_table("media",
        Column("title_id", Integer, ForeignKey("title.id"), primary_key=True, nullable=False),

        Column("capsule",       LargeBinary, nullable=True),
        Column("header",        LargeBinary, nullable=True),
        Column("store_1",       LargeBinary, nullable=True),
        Column("store_2",       LargeBinary, nullable=True),
        Column("store_3",       LargeBinary, nullable=True),
        Column("store_4",       LargeBinary, nullable=True),
        Column("store_5",       LargeBinary, nullable=True),
        Column("store_6",       LargeBinary, nullable=True),
        Column("trailer",       LargeBinary, nullable=True),

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

    op.execute("""
        CREATE OR REPLACE FUNCTION create_title_media()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO media (title_id, created_at, updated_at)
            VALUES (NEW.id, now(), now());
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        DROP TRIGGER IF EXISTS tr_title_create_media ON title;
        CREATE TRIGGER tr_title_create_media
        AFTER INSERT ON title
        FOR EACH ROW
        EXECUTE PROCEDURE create_title_media();
    """)

def downgrade():
    op.drop_table("media")
