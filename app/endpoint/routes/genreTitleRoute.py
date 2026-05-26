from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.GenreTitleModel import GenreTitle
from app.endpoint.schemas.genreTitleSchema import GenreTitleCreate as CreateValidation
from app.endpoint.schemas.genreTitleSchema import GenreTitlePatch as PatchValidation
from app.endpoint.schemas.genreTitleSchema import GenreTitleShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    genre_title = GenreTitle.model_validate(payload)
    session.add(genre_title)
    session.commit()
    session.refresh(genre_title)
    return genre_title



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    genre_titles = session.exec(select(GenreTitle)).all()
    return genre_titles



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    genre_title = session.exec(select(GenreTitle).where(GenreTitle.id == id)).first()
    if not genre_title:
        raise HTTPException(status_code=404, detail="GenreTitle with specified ID doesn't exist")
    return genre_title



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    genre_title = session.exec(select(GenreTitle).where(GenreTitle.id == id)).first()
    if not genre_title:
        raise HTTPException(status_code=404, detail="GenreTitle with specified ID doesn't exist")

    genre_title.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(genre_title)
    session.commit()
    session.refresh(genre_title)
    return genre_title



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    genre_title = session.exec(select(GenreTitle).where(GenreTitle.id == id)).first()

    if not genre_title:
        raise HTTPException(status_code=404, detail="GenreTitle with specified ID doesn't exist")

    session.delete(genre_title)
    session.commit()

    return {"status": "ok"}
