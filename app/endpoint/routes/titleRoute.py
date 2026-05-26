from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.TitleModel import Title
from app.endpoint.schemas.titleSchema import TitleCreate as CreateValidation
from app.endpoint.schemas.titleSchema import TitlePatch as PatchValidation
from app.endpoint.schemas.titleSchema import TitleShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    title = Title.model_validate(payload)
    session.add(title)
    session.commit()
    session.refresh(title)
    return title



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    titles = session.exec(select(Title).where(Title.status)).all()
    return titles



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    title = session.exec(select(Title).where(Title.id == id, Title.status)).first()
    if not title:
        raise HTTPException(status_code=404, detail="Title with specified ID doesn't exist")
    return title



@router.get("/name/{name}", response_model=ShowValidation, status_code=200)
def show_by_name(name: str, session: Session = Depends(get_session)):
    title = session.exec(select(Title).where(Title.name == name, Title.status)).first()
    if not title:
        raise HTTPException(status_code=404, detail="Title with specified NAME doesn't exist")
    return title



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    title = session.exec(select(Title).where(Title.id == id, Title.status)).first()
    if not title:
        raise HTTPException(status_code=404, detail="Title with specified ID doesn't exist")

    title.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(title)
    session.commit()
    session.refresh(title)
    return title



@router.patch("/name/{name}", response_model=ShowValidation)
def update_by_name(name: str, payload: PatchValidation, session: Session = Depends(get_session)):
    title = session.exec(select(Title).where(Title.name == name, Title.status)).first()
    if not title:
        raise HTTPException(status_code=404, detail="Title with specified NAME doesn't exist")

    title.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(title)
    session.commit()
    session.refresh(title)
    return title



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    title = session.exec(select(Title).where(Title.id == id, Title.status)).first()

    if not title:
        raise HTTPException(status_code=404, detail="Title with specified ID doesn't exist")

    title.status = False

    session.add(title)
    session.commit()
    session.refresh(title)

    return {"status": "ok"}
