import re
from datetime import datetime

from fastapi import UploadFile
from pydantic import field_validator
from sqlmodel import SQLModel

from app.endpoint.schemas.countrySchema import CountryShow
from app.endpoint.schemas.walletSchema import WalletShow

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PWD_RE   = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d]).{8,}$")


class CustomerCreate(SQLModel):
    name:     str
    email:    str
    password: str

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


class CustomerPublic(SQLModel):
    name:       str

    country:    CountryShow | None = None
    created_at: datetime    | None = None
    updated_at: datetime    | None = None


class CustomerShow(SQLModel):
    name:       str
    email:      str
    status:     bool

    country:    CountryShow | None = None
    created_at: datetime    | None = None
    updated_at: datetime    | None = None


class CustomerPatch(SQLModel):
    name:         str | None = None
    email:        str | None = None
    password:     str | None = None
    country_code: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        if v is not None and not _PWD_RE.match(v):
            raise ValueError(
                "La contraseña debe tener al menos 8 caracteres, "
                "una mayúscula, una minúscula, un número y un carácter especial"
            )
        return v


class LibraryItem(SQLModel):
    name: str


class FriendItem(SQLModel):
    name: str


class LoginCustomerResponse(SQLModel):
    access_token: str
    token_type:   str = "bearer"  # noqa: S105
    customer:     CustomerShow
    wallet:       WalletShow | None = None


class CustomerImageUpload(SQLModel):
    profile: UploadFile | None = None
    banner:  UploadFile | None = None
