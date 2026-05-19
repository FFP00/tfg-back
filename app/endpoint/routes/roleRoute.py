from app.endpoint.models.RoleModel import Role
from app.endpoint.schemas.roleSchema import RoleCreate as CreateValidation
from app.endpoint.schemas.roleSchema import RolePatch as PatchValidation
from app.endpoint.schemas.roleSchema import RoleShow as ShowValidation
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    role = Role.model_validate(payload)
    session.add(role)
    session.commit()
    session.refresh(role)
    return role



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    roles = session.exec(select(Role)).all()
    return roles



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    role = session.exec(select(Role).where(Role.id == id)).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role with specified ID doesn't exist")
    return role



@router.get("/name/{name}", response_model=ShowValidation, status_code=200)
def show_by_name(name: str, session: Session = Depends(get_session)):
    role = session.exec(select(Role).where(Role.name == name)).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role with specified DNI doesn't exist")
    return role



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    role = session.exec(select(Role).where(Role.id == id)).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role with specified ID doesn't exist")

    role.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(role)
    session.commit()
    session.refresh(role)
    return role



@router.patch("/name/{name}", response_model=ShowValidation)
def update_by_dni(name: str, payload: PatchValidation, session: Session = Depends(get_session)):
    role = session.exec(select(Role).where(Role.name == name)).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role with specified DNI doesn't exist")

    role.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(role)
    session.commit()
    session.refresh(role)
    return role



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    role = session.exec(select(Role).where(Role.id == id)).first()

    if not role:
        raise HTTPException(status_code=404, detail="User with specified ID doesn't exist")

    session.delete(role)
    session.commit()

    return {"status": "ok"}
