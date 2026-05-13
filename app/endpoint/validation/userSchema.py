from datetime import datetime

from sqlmodel import SQLModel

from app.endpoint.validation.roleSchema import RoleShow

'''
class RoleShow(SQLModel):
    id: int
    titulo: str

Esto se tiene que crear en roleSchema e importarlo
'''

class UserCreate(SQLModel):
    name:       str
    lastname:   str
    dni:        str
    email:      str
    password:   str
    status:     bool



class UserShow(SQLModel):
    name:       str
    lastname:   str
    dni:        str
    email:      str
    status:     bool

    role:       Optional[RoleShow]  | None = None
    created_at: datetime            | None = None
    updated_at: datetime            | None = None



class UserPatch(SQLModel):
    name:       Optional[str]   = None
    lastname:   Optional[str]   = None
    dni:        Optional[str]   = None
    email:      Optional[str]   = None
    password:   Optional[str]   = None
    status:     Optional[bool]  = None

    rol_id:     Optional[int]   = None