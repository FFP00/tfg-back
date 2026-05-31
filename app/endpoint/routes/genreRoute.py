from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.config.database import get_session
from app.database.models.GenreModel import Genre
from app.endpoint.schemas.genreSchema import GenreShow

router = APIRouter()


@router.get("/", response_model=list[GenreShow])
def index(session: Session = Depends(get_session)) -> list[Genre]:
    return list(session.exec(select(Genre)).all())
