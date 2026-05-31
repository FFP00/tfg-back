from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response
from pwdlib import PasswordHash
from sqlmodel import Session, or_, select

from app.config.auth import (
    create_access_token,
    oauth2_customer,
    revoke_token,
)
from app.config.database import get_session
from app.database.models.CustomerModel import Customer
from app.database.models.WalletModel import Wallet
from app.endpoint.schemas.authSchema import LoginForm
from app.endpoint.schemas.customerSchema import (
    CustomerCreate,
    CustomerShow,
    LoginCustomerResponse,
)
from app.endpoint.schemas.walletSchema import WalletShow

hasher = PasswordHash.recommended()
router = APIRouter()


@router.post("/register", status_code=201)
def register(
    payload: CustomerCreate, session: Session = Depends(get_session)
) -> Response:
    if session.exec(
        select(Customer).where(
            or_(Customer.email == payload.email, Customer.name == payload.name)
        )
    ).first():
        raise HTTPException(status_code=409, detail="Email o nombre ya registrado")
    customer = Customer(
        name=payload.name,
        email=payload.email,
        password=hasher.hash(payload.password),
    )
    session.add(customer)
    session.commit()
    return Response(status_code=201)


@router.post("/login", response_model=LoginCustomerResponse)
def login(
    form: Annotated[LoginForm, Form()], session: Session = Depends(get_session)
) -> LoginCustomerResponse:
    customer = session.exec(
        select(Customer).where(
            or_(Customer.email == form.username, Customer.name == form.username),
            Customer.status,
        )
    ).first()
    if not customer or not hasher.verify(form.password, customer.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    wallet = session.exec(
        select(Wallet).where(Wallet.customer_id == customer.id)
    ).first()
    token = create_access_token({"sub": str(customer.id), "role": "customer"}, session)
    return LoginCustomerResponse(
        access_token=token,
        customer=CustomerShow.model_validate(customer, from_attributes=True),
        wallet=WalletShow.model_validate(wallet, from_attributes=True)
        if wallet
        else None,
    )


@router.post("/logout", status_code=204)
def logout(
    token: str = Depends(oauth2_customer), session: Session = Depends(get_session)
) -> Response:
    revoke_token(token, session)
    return Response(status_code=204)
