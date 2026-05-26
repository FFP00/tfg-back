from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.ImageModel import Image
from app.endpoint.schemas.imageSchema import ImageCreate as CreateValidation
from app.endpoint.schemas.imageSchema import ImagePatch as PatchValidation
from app.endpoint.schemas.imageSchema import ImageShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    image = Image.model_validate(payload)
    session.add(image)
    session.commit()
    session.refresh(image)
    return image



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    images = session.exec(select(Image)).all()
    return images



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    image = session.exec(select(Image).where(Image.id == id)).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image with specified ID doesn't exist")
    return image



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    image = session.exec(select(Image).where(Image.id == id)).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image with specified ID doesn't exist")

    image.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(image)
    session.commit()
    session.refresh(image)
    return image



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    image = session.exec(select(Image).where(Image.id == id)).first()

    if not image:
        raise HTTPException(status_code=404, detail="Image with specified ID doesn't exist")

    session.delete(image)
    session.commit()

    return {"status": "ok"}
