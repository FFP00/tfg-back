from sqlalchemy import Column, DateTime, Integer, String

from alembic import op

# revision identifiers, used by Alembic.
revision        = "000"
down_revision   = None # Cuando hagamos la revision 002 en este campo ponemos la anterior 001
branch_labels   = None
depends_on      = None


def upgrade():
    op.create_table("roles",

        Column("id", Integer, primary_key=True, autoincrement=True, nullable=False),
        Column("name", String, nullable=False),

        Column("created_at", DateTime(timezone=True), default=None),
        Column("updated_at", DateTime(timezone=True), default=None),
    )

def downgrade():
    op.drop_table("roles")
