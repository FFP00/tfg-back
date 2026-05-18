from sqlmodel import SQLModel


class RoleCreate(SQLModel):
    name:   str | None = None

class RoleShow(SQLModel):
    name:   str | None = None

class RolePatch(SQLModel):
    name:   str | None = None

