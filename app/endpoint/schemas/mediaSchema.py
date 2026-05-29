import base64

from pydantic import Base64Bytes, field_serializer
from sqlmodel import SQLModel


class MediaCreate(SQLModel):
    capsule:    Base64Bytes
    header:     Base64Bytes
    store_1:    Base64Bytes
    store_2:    Base64Bytes | None = None
    store_3:    Base64Bytes | None = None
    store_4:    Base64Bytes | None = None
    store_5:    Base64Bytes | None = None
    store_6:    Base64Bytes | None = None
    trailer:    Base64Bytes | None = None


class MediaShowLite(SQLModel):
    id: int | None = None


class MediaShow(SQLModel):
    id:         int | None = None
    capsule:    bytes
    header:     bytes
    store_1:    bytes
    store_2:    bytes | None = None
    store_3:    bytes | None = None
    store_4:    bytes | None = None
    store_5:    bytes | None = None
    store_6:    bytes | None = None
    trailer:    bytes | None = None

    @field_serializer(
        "capsule", "header",
        "store_1", "store_2", "store_3", "store_4", "store_5", "store_6",
        "trailer",
        when_used="json",
    )
    def _encode_base64(self, v: bytes | None) -> str | None:
        if v is None:
            return None
        return base64.b64encode(v).decode()


class MediaPatch(SQLModel):
    capsule:    Base64Bytes | None = None
    header:     Base64Bytes | None = None
    store_1:    Base64Bytes | None = None
    store_2:    Base64Bytes | None = None
    store_3:    Base64Bytes | None = None
    store_4:    Base64Bytes | None = None
    store_5:    Base64Bytes | None = None
    store_6:    Base64Bytes | None = None
    trailer:    Base64Bytes | None = None
