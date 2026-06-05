from decimal import Decimal

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.config.auth import get_current_customer
from app.config.database import get_session
from app.config.settings import settings
from app.database.models.CustomerModel import Customer
from app.database.models.WalletModel import Wallet
from app.endpoint.schemas.walletSchema import WalletShow

router = APIRouter()


class CheckoutPayload(BaseModel):
    amount: Decimal


class CheckoutResponse(BaseModel):
    checkout_url: str


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    payload: CheckoutPayload,
    current: Customer = Depends(get_current_customer),
) -> CheckoutResponse:
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="El importe debe ser positivo")
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe no configurado")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    amount_cents = int(payload.amount * 100)

    checkout = stripe.checkout.Session.create(
        payment_method_types = ["card"],
        line_items           = [{
            "price_data": {
                "currency":     "usd",
                "unit_amount":  amount_cents,
                "product_data": {"name": f"Recarga de saldo — {current.user.name if current.user else 'Burnt'}"},
            },
            "quantity": 1,
        }],
        mode        = "payment",
        success_url = f"{settings.STRIPE_SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}&user_id={current.user_id}",
        cancel_url  = settings.STRIPE_CANCEL_URL,
        metadata    = {"customer_user_id": str(current.user_id), "amount": str(payload.amount)},
    )
    return CheckoutResponse(checkout_url=checkout.url)


@router.get("/success", response_model=WalletShow)
def confirm_checkout(
    session_id: str,
    current:    Customer = Depends(get_current_customer),
    db:         Session  = Depends(get_session),
) -> WalletShow:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe no configurado")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        checkout = stripe.checkout.Session.retrieve(session_id)
    except stripe.StripeError as exc:
        raise HTTPException(status_code=400, detail="Sesión de pago inválida") from exc

    if checkout.payment_status != "paid":
        raise HTTPException(status_code=402, detail="El pago no se ha completado")

    metadata: dict = checkout.metadata._data if checkout.metadata else {}
    meta_uid = int(metadata.get("customer_user_id", 0))
    if meta_uid != current.user_id:
        raise HTTPException(status_code=403, detail="Sesión de pago no pertenece a este usuario")

    amount = Decimal(metadata.get("amount", "0"))
    wallet = db.get(Wallet, current.user_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet no encontrada")

    wallet.balance = (wallet.balance or Decimal(0)) + amount
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return WalletShow.model_validate(wallet, from_attributes=True)
