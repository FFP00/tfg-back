from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.auth import get_current_customer
from app.config.database import get_session
from app.database.models.CustomerModel import Customer
from app.database.models.CustomerTitleModel import CustomerTitle
from app.database.models.TitleModel import Title
from app.database.models.TitleTransactionModel import TitleTransaction
from app.database.models.TransactionModel import Transaction
from app.database.models.WalletModel import Wallet
from app.endpoint.schemas.transactionSchema import (
    PurchasedTitleItem,
    PurchasePayload,
    PurchaseResponse,
    TransactionHistoryItem,
)

router = APIRouter()


@router.post("/", response_model=PurchaseResponse)
def purchase(
    payload: PurchasePayload,
    current: Customer = Depends(get_current_customer),
    session: Session = Depends(get_session),
) -> PurchaseResponse:
    if not payload.titles:
        raise HTTPException(status_code=400, detail="Lista de títulos vacía")

    wallet = session.exec(
        select(Wallet).where(Wallet.customer_id == current.id)
    ).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet no encontrada")

    owned_ids = {
        ct.title_id
        for ct in session.exec(
            select(CustomerTitle).where(CustomerTitle.customer_id == current.id)
        ).all()
    }

    titles_to_buy: list[Title] = []
    for name in payload.titles:
        title = session.exec(
            select(Title).where(Title.name == name, Title.status)
        ).first()
        if not title:
            raise HTTPException(
                status_code=404, detail=f"Título '{name}' no encontrado o no disponible"
            )
        if title.id in owned_ids:
            raise HTTPException(
                status_code=409, detail=f"Ya tienes '{name}' en tu biblioteca"
            )
        titles_to_buy.append(title)

    def _final_price(t: Title) -> Decimal:
        return t.release_price * (1 - Decimal(t.actual_discount) / 100)

    total = sum(_final_price(t) for t in titles_to_buy)

    if (wallet.balance or Decimal(0)) < total:
        raise HTTPException(status_code=402, detail="Balance insuficiente")

    transaction = Transaction(customer_id=current.id)
    session.add(transaction)
    session.flush()

    for title in titles_to_buy:
        price = _final_price(title)
        session.add(
            TitleTransaction(
                title_id=title.id,
                transaction_id=transaction.id,
                price=price,
                discount=title.actual_discount,
            )
        )
        session.add(CustomerTitle(title_id=title.id, customer_id=current.id))

    wallet.balance = (wallet.balance or Decimal(0)) - total
    session.add(wallet)
    session.commit()

    return PurchaseResponse(
        titles_purchased=len(titles_to_buy),
        total_spent=total,
        wallet_balance=wallet.balance,
    )


@router.get("/me", response_model=list[TransactionHistoryItem])
def history(
    current: Customer = Depends(get_current_customer),
    session: Session = Depends(get_session),
) -> list[TransactionHistoryItem]:
    transactions = session.exec(
        select(Transaction).where(Transaction.customer_id == current.id)
    ).all()

    result = []
    for tx in transactions:
        items = session.exec(
            select(TitleTransaction).where(TitleTransaction.transaction_id == tx.id)
        ).all()
        purchased = []
        for item in items:
            title = session.get(Title, item.title_id)
            if title:
                purchased.append(
                    PurchasedTitleItem(
                        name=title.name,
                        price_paid=item.price,
                        discount_applied=item.discount,
                    )
                )
        result.append(
            TransactionHistoryItem(created_at=tx.created_at, titles=purchased)
        )
    return result
