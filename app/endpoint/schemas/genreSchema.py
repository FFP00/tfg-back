from sqlmodel import SQLModel


class GenreCreate(SQLModel):
    name:   str


class GenreShow(SQLModel):
    id:     int | None = None
    name:   str


class GenrePatch(SQLModel):
    name:   str | None = None
