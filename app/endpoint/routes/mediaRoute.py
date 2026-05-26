from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.MediaModel import Media
from app.endpoint.schemas.mediaSchema import MediaCreate as CreateValidation
from app.endpoint.schemas.mediaSchema import MediaPatch as PatchValidation
from app.endpoint.schemas.mediaSchema import MediaShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    media = Media.model_validate(payload)
    session.add(media)
    session.commit()
    session.refresh(media)
    return media



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    medias = session.exec(select(Media)).all()
    return medias



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    media = session.exec(select(Media).where(Media.id == id)).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media with specified ID doesn't exist")
    return media



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    media = session.exec(select(Media).where(Media.id == id)).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media with specified ID doesn't exist")

    media.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(media)
    session.commit()
    session.refresh(media)
    return media



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    media = session.exec(select(Media).where(Media.id == id)).first()

    if not media:
        raise HTTPException(status_code=404, detail="Media with specified ID doesn't exist")

    session.delete(media)
    session.commit()

    return {"status": "ok"}
