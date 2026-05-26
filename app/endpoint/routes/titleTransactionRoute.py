from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.TitleTransactionModel import TitleTransaction
from app.endpoint.schemas.titleTransactionSchema import (
    TitleTransactionCreate as CreateValidation,
)
from app.endpoint.schemas.titleTransactionSchema import (
    TitleTransactionPatch as PatchValidation,
)
from app.endpoint.schemas.titleTransactionSchema import (
    TitleTransactionShow as ShowValidation,
)

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    title_transaction = TitleTransaction.model_validate(payload)
    session.add(title_transaction)
    session.commit()
    session.refresh(title_transaction)
    return title_transaction



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    title_transactions = session.exec(select(TitleTransaction)).all()
    return title_transactions



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    title_transaction = session.exec(select(TitleTransaction).where(TitleTransaction.id == id)).first()
    if not title_transaction:
        raise HTTPException(status_code=404, detail="TitleTransaction with specified ID doesn't exist")
    return title_transaction



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    title_transaction = session.exec(select(TitleTransaction).where(TitleTransaction.id == id)).first()
    if not title_transaction:
        raise HTTPException(status_code=404, detail="TitleTransaction with specified ID doesn't exist")

    title_transaction.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(title_transaction)
    session.commit()
    session.refresh(title_transaction)
    return title_transaction



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    title_transaction = session.exec(select(TitleTransaction).where(TitleTransaction.id == id)).first()

    if not title_transaction:
        raise HTTPException(status_code=404, detail="TitleTransaction with specified ID doesn't exist")

    session.delete(title_transaction)
    session.commit()

    return {"status": "ok"}
