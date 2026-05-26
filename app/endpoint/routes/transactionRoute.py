from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.TransactionModel import Transaction
from app.endpoint.schemas.transactionSchema import TransactionCreate as CreateValidation
from app.endpoint.schemas.transactionSchema import TransactionPatch as PatchValidation
from app.endpoint.schemas.transactionSchema import TransactionShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    transaction = Transaction.model_validate(payload)
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    transactions = session.exec(select(Transaction)).all()
    return transactions



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    transaction = session.exec(select(Transaction).where(Transaction.id == id)).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction with specified ID doesn't exist")
    return transaction



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    transaction = session.exec(select(Transaction).where(Transaction.id == id)).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction with specified ID doesn't exist")

    transaction.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    transaction = session.exec(select(Transaction).where(Transaction.id == id)).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction with specified ID doesn't exist")

    session.delete(transaction)
    session.commit()

    return {"status": "ok"}
