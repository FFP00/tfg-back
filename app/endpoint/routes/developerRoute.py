from fastapi import APIRouter, Depends, HTTPException
from pwdlib import PasswordHash
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.DeveloperModel import Developer
from app.endpoint.schemas.developerSchema import DeveloperCreate as CreateValidation
from app.endpoint.schemas.developerSchema import DeveloperPatch as PatchValidation
from app.endpoint.schemas.developerSchema import DeveloperShow as ShowValidation

# Argon2 es el estándar de oro actual para contraseñas
hasher = PasswordHash.recommended()
router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    developer = Developer.model_validate(payload)
    developer.password = hasher.hash(developer.password)
    session.add(developer)
    session.commit()
    session.refresh(developer)
    return developer



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    developers = session.exec(select(Developer).where(Developer.status)).all()
    return developers



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    developer = session.exec(select(Developer).where(Developer.id == id, Developer.status)).first()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer with specified ID doesn't exist")
    return developer



@router.get("/name/{name}", response_model=ShowValidation, status_code=200)
def show_by_name(name: str, session: Session = Depends(get_session)):
    developer = session.exec(select(Developer).where(Developer.name == name, Developer.status)).first()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer with specified NAME doesn't exist")
    return developer



@router.get("/email/{email}", response_model=ShowValidation, status_code=200)
def show_by_email(email: str, session: Session = Depends(get_session)):
    developer = session.exec(select(Developer).where(Developer.email == email, Developer.status)).first()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer with specified EMAIL doesn't exist")
    return developer



@router.get("/support_email/{support_email}", response_model=ShowValidation, status_code=200)
def show_by_support_email(support_email: str, session: Session = Depends(get_session)):
    developer = session.exec(select(Developer).where(Developer.support_email == support_email, Developer.status)).first()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer with specified SUPPORT_EMAIL doesn't exist")
    return developer



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    developer = session.exec(select(Developer).where(Developer.id == id, Developer.status)).first()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer with specified ID doesn't exist")

    developer.sqlmodel_update(payload.model_dump(exclude_unset=True))

    if payload.password is not None:
        developer.password = hasher.hash(developer.password)
    session.add(developer)
    session.commit()
    session.refresh(developer)
    return developer



@router.patch("/name/{name}", response_model=ShowValidation)
def update_by_name(name: str, payload: PatchValidation, session: Session = Depends(get_session)):
    developer = session.exec(select(Developer).where(Developer.name == name, Developer.status)).first()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer with specified NAME doesn't exist")

    developer.sqlmodel_update(payload.model_dump(exclude_unset=True))

    if payload.password is not None:
        developer.password = hasher.hash(developer.password)
    session.add(developer)
    session.commit()
    session.refresh(developer)
    return developer



@router.patch("/email/{email}", response_model=ShowValidation)
def update_by_email(email: str, payload: PatchValidation, session: Session = Depends(get_session)):
    developer = session.exec(select(Developer).where(Developer.email == email, Developer.status)).first()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer with specified EMAIL doesn't exist")

    developer.sqlmodel_update(payload.model_dump(exclude_unset=True))

    if payload.password is not None:
        developer.password = hasher.hash(developer.password)
    session.add(developer)
    session.commit()
    session.refresh(developer)
    return developer



@router.patch("/support_email/{support_email}", response_model=ShowValidation)
def update_by_support_email(support_email: str, payload: PatchValidation, session: Session = Depends(get_session)):
    developer = session.exec(select(Developer).where(Developer.support_email == support_email, Developer.status)).first()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer with specified SUPPORT_EMAIL doesn't exist")

    developer.sqlmodel_update(payload.model_dump(exclude_unset=True))

    if payload.password is not None:
        developer.password = hasher.hash(developer.password)
    session.add(developer)
    session.commit()
    session.refresh(developer)
    return developer



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    developer = session.exec(select(Developer).where(Developer.id == id, Developer.status)).first()

    if not developer:
        raise HTTPException(status_code=404, detail="Developer with specified ID doesn't exist")

    developer.status = False

    session.add(developer)
    session.commit()
    session.refresh(developer)

    return {"status": "ok"}
