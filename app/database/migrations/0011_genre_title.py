from sqlalchemy import Column, DateTime, ForeignKey, Integer, func

from alembic import op

revision        = "011"
down_revision   = "010"
branch_labels   = None
depends_on      = None


def upgrade():
    op.create_table("genre_title",

        Column("id",       Integer, primary_key=True, autoincrement=True, nullable=False),

        Column("title_id", Integer, ForeignKey("title.id"),  nullable=False),
        Column("genre_id", Integer, ForeignKey("genre.id"),  nullable=False),

        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False, default=None),
    )


def downgrade():
    op.drop_table("genre_title")
