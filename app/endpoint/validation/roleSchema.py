from sqlmodel import SQLModel


class RoleShow(SQLModel):
    id:     int
    name:   str
