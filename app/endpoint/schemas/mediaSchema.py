from sqlmodel import SQLModel


class MediaCreate(SQLModel):
    path_300x450:   str
    path_600x900:   str


class MediaShow(SQLModel):
    path_300x450:   str
    path_600x900:   str


class MediaPatch(SQLModel):
    path_300x450:   str | None = None
    path_600x900:   str | None = None
