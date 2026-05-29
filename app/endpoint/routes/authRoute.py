from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlmodel import Session, select

from app.config.auth import (
    create_access_token,
    get_current_customer,
    get_current_developer,
    oauth2_customer,
    oauth2_developer,
    revoke_token,
)
from app.config.database import get_session
from app.endpoint.models.CustomerModel import Customer
from app.endpoint.models.DeveloperModel import Developer
from app.endpoint.schemas.authSchema import TokenResponse
from app.endpoint.schemas.customerSchema import CustomerCreate as CustomerRegister
from app.endpoint.schemas.customerSchema import CustomerShow
from app.endpoint.schemas.developerSchema import DeveloperCreate as DeveloperRegister
from app.endpoint.schemas.developerSchema import DeveloperShow

hasher = PasswordHash.recommended()
router = APIRouter()



# ── Customer ──────────────────────────────────────────────────────────────────

@router.post("/customer/register", response_model=CustomerShow, status_code=201)
def customer_register(payload: CustomerRegister, session: Session = Depends(get_session)):
    if session.exec(select(Customer).where(Customer.email == payload.email)).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")
    customer = Customer.model_validate(payload)
    customer.password = hasher.hash(customer.password)
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer



@router.post("/customer/login", response_model=TokenResponse)
def customer_login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    customer = session.exec(select(Customer).where(Customer.email == form.username, Customer.status)).first()
    if not customer or not hasher.verify(form.password, customer.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return TokenResponse(access_token=create_access_token({"sub": customer.id, "role": "customer"}, session), role="customer")



@router.get("/customer/me", response_model=CustomerShow)
def customer_me(current: Customer = Depends(get_current_customer)):
    return current



@router.post("/customer/logout")
def customer_logout(token: str = Depends(oauth2_customer), session: Session = Depends(get_session)):
    revoke_token(token, session)
    return {"detail": "Sesión cerrada"}



# ── Developer ─────────────────────────────────────────────────────────────────

@router.post("/developer/register", response_model=DeveloperShow, status_code=201)
def developer_register(payload: DeveloperRegister, session: Session = Depends(get_session)):
    if session.exec(select(Developer).where(Developer.email == payload.email)).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")
    developer = Developer.model_validate(payload)
    developer.password = hasher.hash(developer.password)
    session.add(developer)
    session.commit()
    session.refresh(developer)
    return developer



@router.post("/developer/login", response_model=TokenResponse)
def developer_login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    developer = session.exec(select(Developer).where(Developer.email == form.username, Developer.status)).first()
    if not developer or not hasher.verify(form.password, developer.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return TokenResponse(access_token=create_access_token({"sub": developer.id, "role": "developer"}, session), role="developer")



@router.get("/developer/me", response_model=DeveloperShow)
def developer_me(current: Developer = Depends(get_current_developer)):
    return current



@router.post("/developer/logout")
def developer_logout(token: str = Depends(oauth2_developer), session: Session = Depends(get_session)):
    revoke_token(token, session)
    return {"detail": "Sesión cerrada"}
