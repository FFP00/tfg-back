from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.GenreModel import Genre
from app.endpoint.schemas.genreSchema import GenreCreate as CreateValidation
from app.endpoint.schemas.genreSchema import GenrePatch as PatchValidation
from app.endpoint.schemas.genreSchema import GenreShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    genre = Genre.model_validate(payload)
    session.add(genre)
    session.commit()
    session.refresh(genre)
    return genre



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    genres = session.exec(select(Genre)).all()
    return genres



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    genre = session.exec(select(Genre).where(Genre.id == id)).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre with specified ID doesn't exist")
    return genre



@router.get("/name/{name}", response_model=ShowValidation, status_code=200)
def show_by_name(name: str, session: Session = Depends(get_session)):
    genre = session.exec(select(Genre).where(Genre.name == name)).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre with specified NAME doesn't exist")
    return genre



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    genre = session.exec(select(Genre).where(Genre.id == id)).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre with specified ID doesn't exist")

    genre.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(genre)
    session.commit()
    session.refresh(genre)
    return genre



@router.patch("/name/{name}", response_model=ShowValidation)
def update_by_name(name: str, payload: PatchValidation, session: Session = Depends(get_session)):
    genre = session.exec(select(Genre).where(Genre.name == name)).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre with specified NAME doesn't exist")

    genre.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(genre)
    session.commit()
    session.refresh(genre)
    return genre



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    genre = session.exec(select(Genre).where(Genre.id == id)).first()

    if not genre:
        raise HTTPException(status_code=404, detail="Genre with specified ID doesn't exist")

    session.delete(genre)
    session.commit()

    return {"status": "ok"}
