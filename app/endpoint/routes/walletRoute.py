from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.WalletModel import Wallet
from app.endpoint.schemas.walletSchema import WalletCreate as CreateValidation
from app.endpoint.schemas.walletSchema import WalletPatch as PatchValidation
from app.endpoint.schemas.walletSchema import WalletShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    wallet = Wallet.model_validate(payload)
    session.add(wallet)
    session.commit()
    session.refresh(wallet)
    return wallet



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    wallets = session.exec(select(Wallet)).all()
    return wallets



@router.get("/{customer_id}", response_model=ShowValidation, status_code=200)
def show_by_customer_id(customer_id: int, session: Session = Depends(get_session)):
    wallet = session.exec(select(Wallet).where(Wallet.customer_id == customer_id)).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet with specified CUSTOMER_ID doesn't exist")
    return wallet



@router.patch("/{customer_id}", response_model=ShowValidation)
def update(customer_id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    wallet = session.exec(select(Wallet).where(Wallet.customer_id == customer_id)).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet with specified CUSTOMER_ID doesn't exist")

    wallet.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(wallet)
    session.commit()
    session.refresh(wallet)
    return wallet



@router.delete("/{customer_id}")
def delete(customer_id: int, session: Session = Depends(get_session)):
    wallet = session.exec(select(Wallet).where(Wallet.customer_id == customer_id)).first()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet with specified CUSTOMER_ID doesn't exist")

    session.delete(wallet)
    session.commit()

    return {"status": "ok"}
