from sqlmodel import SQLModel

from app.endpoint.schemas.genreSchema import GenreShow
from app.endpoint.schemas.titleSchema import TitleShow


class GenreTitleCreate(SQLModel):
    title_id:   int
    genre_id:   int


class GenreTitleShow(SQLModel):
    title_id:   int
    genre_id:   int

    title:      TitleShow | None = None
    genre:      GenreShow | None = None


class GenreTitlePatch(SQLModel):
    title_id:   int | None = None
    genre_id:   int | None = None
