from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.connection import get_session 
from app.database.models.user import User

from app.endpoint.validation.userSchema import (
    UserCreate  as CreateValidation,
    UserShow    as ShowValidation,
    UserPatch   as PatchValidation
)

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
'''
'''
    user = User.model_validate(payload)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
'''
'''
    users = session.exec(select(User).where(User.status == True)).all()
    return users



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
'''
'''
    user = session.exec(select(User).where(User.id == id, User.status == True)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with specified ID doesn't exist")
    return user



@router.get("/dni/{dni}", response_model=ShowValidation, status_code=200)
def show_by_dni(dni: str, session: Session = Depends(get_session)):
'''
'''
    user = session.exec(select(User).where(User.dni == dni, User.status == True)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with specified DNI doesn't exist")
    return user



@router.get("/email/{email}", response_model=ShowValidation, status_code=200)
def show_by_email(email: str, session: Session = Depends(get_session)):
'''
'''
    user = session.exec(select(User).where(User.email == email, User.status == True)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with specified EMAIL doesn't exist")
    return user



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
'''
'''
    user = session.exec(select(User).where(User.id == id, User.status == True)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with specified ID doesn't exist")

    user.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(user)
    session.commit()
    session.refresh(user)
    return user



@router.patch("/dni/{dni}", response_model=ShowValidation)
def update_by_dni(dni: str, payload: PatchValidation, session: Session = Depends(get_session)):
'''
'''
    user = session.exec(select(User).where(User.dni == dni, User.status == True)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with specified DNI doesn't exist")

    user.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(user)
    session.commit()
    session.refresh(user)
    return user



@router.patch("/email/{email}", response_model=ShowValidation)
def update_by_email(email: str, payload: PatchValidation, session: Session = Depends(get_session)):
'''
'''
    user = session.exec(select(User).where(User.email == email, User.status == True)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with specified EMAIL doesn't exist")

    user.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(user)
    session.commit()
    session.refresh(user)
    return user



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
'''
'''
    user = session.exec(select(User).where(User.id == id, User.status == True)).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User with specified ID doesn't exist")

    user.status = False 

    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {"status": "ok"}
