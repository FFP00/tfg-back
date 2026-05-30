from sqlmodel import SQLModel


class GenreCreate(SQLModel):
    name:   str


class GenreShow(SQLModel):
    name:   str


class GenrePatch(SQLModel):
    name:   str | None = None
