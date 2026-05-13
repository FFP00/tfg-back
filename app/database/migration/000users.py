from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from alembic import op

# revision identifiers, used by Alembic.
revision        = "001"
down_revision   = None # Cuando hagamos la revision 002 en este campo ponemos la anterior 001
branch_labels   = None
depends_on      = None


def upgrade():
    op.create_table("users",

        Column("id",            Integer, primary_key=True, autoincrement=True, nullable=False),
        Column("name",          String, nullable=False),
        Column("lastname",      String, nullable=False),
        Column("dni",           String, nullable=False, unique=True),
        Column("email",         String, nullable=False, unique=True),
        Column("password",      String, nullable=False),
        Column("status",        Boolean, default=False, nullable=False),

        Column("role_id",       Integer, ForeignKey("roles.id"), nullable=False),
        Column("created_at",    DateTime(timezone=True), default=None),
        Column("updated_at",    DateTime(timezone=True), default=None),
    )

def downgrade():
    op.drop_table("users")
