from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.FriendshipModel import Friendship
from app.endpoint.schemas.friendshipSchema import FriendshipCreate as CreateValidation
from app.endpoint.schemas.friendshipSchema import FriendshipPatch as PatchValidation
from app.endpoint.schemas.friendshipSchema import FriendshipShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    friendship = Friendship.model_validate(payload)
    session.add(friendship)
    session.commit()
    session.refresh(friendship)
    return friendship



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    friendships = session.exec(select(Friendship)).all()
    return friendships



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    friendship = session.exec(select(Friendship).where(Friendship.id == id)).first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship with specified ID doesn't exist")
    return friendship



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    friendship = session.exec(select(Friendship).where(Friendship.id == id)).first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship with specified ID doesn't exist")

    friendship.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(friendship)
    session.commit()
    session.refresh(friendship)
    return friendship



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    friendship = session.exec(select(Friendship).where(Friendship.id == id)).first()

    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship with specified ID doesn't exist")

    session.delete(friendship)
    session.commit()

    return {"status": "ok"}
