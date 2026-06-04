from datetime import datetime

from fastapi import UploadFile
from pydantic import field_validator
from sqlmodel import SQLModel

from app.endpoint.schemas.countrySchema import CountryShow
from app.endpoint.schemas.userSchema import _EMAIL_RE, _PWD_RE


class DeveloperCreate(SQLModel):
    name:          str
    email:         str
    support_email: str
    password:      str
    country_code:  str
    website_url:   str | None = None

    @field_validator("email", "support_email")
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


class DeveloperPublic(SQLModel):
    name:          str
    support_email: str
    website_url:   str         | None = None
    country:       CountryShow | None = None
    created_at:    datetime    | None = None
    updated_at:    datetime    | None = None


class DeveloperShow(SQLModel):
    name:          str
    email:         str
    support_email: str
    website_url:   str         | None = None
    status:        bool
    country:       CountryShow | None = None
    created_at:    datetime    | None = None
    updated_at:    datetime    | None = None


class DeveloperPatch(SQLModel):
    name:          str | None = None
    email:         str | None = None
    support_email: str | None = None
    password:      str | None = None
    website_url:   str | None = None
    country_code:  str | None = None

    @field_validator("email", "support_email")
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


class LoginDeveloperResponse(SQLModel):
    access_token: str
    token_type:   str = "bearer"  # noqa: S105
    developer:    DeveloperShow


class DeveloperImageUpload(SQLModel):
    profile: UploadFile | None = None
    banner:  UploadFile | None = None
