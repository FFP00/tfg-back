import re
from datetime import datetime

from pydantic import field_validator
from sqlmodel import SQLModel

from app.endpoint.schemas.countrySchema import CountryShow

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PWD_RE   = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d]).{8,}$")


class UserCreate(SQLModel):
    name:         str
    email:        str
    password:     str
    country_code: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("Email inválido")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not _PWD_RE.match(v):
            raise ValueError(
                "La contraseña debe tener al menos 8 caracteres, "
                "una mayúscula, una minúscula, un número y un carácter especial"
            )
        return v


class UserPublic(SQLModel):
    name:       str
    country:    CountryShow | None = None
    created_at: datetime    | None = None


class UserShow(SQLModel):
    name:       str
    email:      str
    country:    CountryShow | None = None
    created_at: datetime    | None = None
    updated_at: datetime    | None = None


class UserPatch(SQLModel):
    name:         str | None = None
    email:        str | None = None
    password:     str | None = None
    country_code: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None and not _EMAIL_RE.match(v):
            raise ValueError("Email inválido")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        if v is not None and not _PWD_RE.match(v):
            raise ValueError(
                "La contraseña debe tener al menos 8 caracteres, "
                "una mayúscula, una minúscula, un número y un carácter especial"
            )
        return v
