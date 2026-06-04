from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response
from pwdlib import PasswordHash
from sqlmodel import Session, or_, select

from app.config.auth import create_access_token, oauth2_customer, revoke_token
from app.config.database import get_session
from app.database.models.CountryModel import Country
from app.database.models.CustomerModel import Customer
from app.database.models.UserModel import User
from app.database.models.WalletModel import Wallet
from app.endpoint.schemas.authSchema import LoginForm
from app.endpoint.schemas.countrySchema import CountryShow
from app.endpoint.schemas.customerSchema import CustomerCreate as CreateValidation
from app.endpoint.schemas.customerSchema import CustomerShow as ShowValidation
from app.endpoint.schemas.customerSchema import LoginCustomerResponse
from app.endpoint.schemas.walletSchema import WalletShow

hasher = PasswordHash.recommended()
router = APIRouter()


def _build_show(customer: Customer) -> ShowValidation:
    u = customer.user
    return ShowValidation(
        name       = u.name       if u else "",
        email      = u.email      if u else "",
        status     = customer.status,
        country    = CountryShow.model_validate(u.country, from_attributes=True) if u and u.country else None,
        created_at = customer.created_at,
        updated_at = customer.updated_at,
    )


@router.post("/register", status_code=201)
def register(payload: CreateValidation, session: Session = Depends(get_session)) -> Response:
    country = session.exec(select(Country).where(Country.code == payload.country_code)).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country no encontrado")
    if session.exec(
        select(User).where(or_(User.email == payload.email, User.name == payload.name))
    ).first():
        raise HTTPException(status_code=409, detail="Email o nombre ya registrado")
    user = User(
        name=payload.name,
        email=payload.email,
        password=hasher.hash(payload.password),
        country_id=country.id,
        type="CUS",
    )
    session.add(user)
    session.flush()
    session.add(Customer(user_id=user.id))
    session.commit()
    return Response(status_code=201)


@router.post("/login", response_model=LoginCustomerResponse)
def login(
    form: Annotated[LoginForm, Form()], session: Session = Depends(get_session)
) -> LoginCustomerResponse:
    user = session.exec(
        select(User).where(
            or_(User.email == form.username, User.name == form.username),
            User.type == "CUS",
        )
    ).first()
    customer = session.get(Customer, user.id) if user else None
    if not user or not customer or not customer.status or not hasher.verify(form.password, user.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    wallet = session.get(Wallet, user.id)
    token  = create_access_token({"sub": str(user.id), "role": "customer"}, user.id, session)
    return LoginCustomerResponse(
        access_token = token,
        customer     = _build_show(customer),
        wallet       = WalletShow.model_validate(wallet, from_attributes=True) if wallet else None,
    )


@router.post("/logout", status_code=204)
def logout(
    token: str = Depends(oauth2_customer), session: Session = Depends(get_session)
) -> Response:
    revoke_token(token, session)
    return Response(status_code=204)
