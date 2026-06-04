from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from pwdlib import PasswordHash
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.config.database import get_session
from app.config.errors import human_error
from app.config.templates import templates
from app.database.models.CountryModel import Country
from app.database.models.CustomerModel import Customer
from app.database.models.UserModel import User
from app.database.models.WalletModel import Wallet

hasher = PasswordHash.recommended()

_PAGE = 20

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error":   request.query_params.get("error"),
        "form":    {},
        **kwargs,
    }


def _countries(session: Session):
    return session.exec(select(Country).order_by(Country.english_name)).all()


@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Customer).join(User, Customer.user_id == User.id)
    count_q = select(func.count()).select_from(Customer).join(User, Customer.user_id == User.id)
    if search:
        cond    = col(User.name).ilike(f"%{search}%") | col(User.email).ilike(f"%{search}%")
        q       = q.where(cond)
        count_q = count_q.where(cond)
    total     = session.exec(count_q).one()
    customers = session.exec(q.order_by(Customer.created_at.desc()).offset((page - 1) * _PAGE).limit(_PAGE)).all()
    return templates.TemplateResponse(request, "customer/index.html", _ctx(request,
        customers=customers, search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(request, "customer/create.html", _ctx(request, countries=_countries(session)))


@router.post("/")
def store(
    request:    Request,
    name:       str     = Form(...),
    email:      str     = Form(...),
    password:   str     = Form(...),
    country_id: str     = Form(""),
    session:    Session = Depends(get_session),
):
    try:
        user = User(
            name       = name,
            email      = email,
            password   = hasher.hash(password),
            country_id = int(country_id) if country_id else None,
            type       = "CUS",
        )
        session.add(user)
        session.flush()
        session.add(Customer(user_id=user.id))
        session.commit()
        return RedirectResponse("/views/customer/?success=Customer+creado+correctamente", status_code=302)
    except Exception as e:
        session.rollback()
        return templates.TemplateResponse(request, "customer/create.html",
            _ctx(request, error=human_error(e), countries=_countries(session),
                 form={"name": name, "email": email, "country_id": country_id}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    customer = session.get(Customer, id)
    if not customer:
        return RedirectResponse("/views/customer/?error=Customer+no+encontrado", status_code=302)
    wallet = session.get(Wallet, id)
    return templates.TemplateResponse(request, "customer/show.html", _ctx(request, customer=customer, wallet=wallet))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    customer = session.get(Customer, id)
    if not customer:
        return RedirectResponse("/views/customer/?error=Customer+no+encontrado", status_code=302)
    wallet = session.get(Wallet, id)
    return templates.TemplateResponse(request, "customer/edit.html",
        _ctx(request, customer=customer, wallet=wallet, countries=_countries(session)),
    )


@router.post("/{id}/update")
def update(
    id:         int,
    request:    Request,
    name:       str     = Form(...),
    email:      str     = Form(...),
    password:   str     = Form(""),
    status:     str     = Form("true"),
    country_id: str     = Form(""),
    balance:    str     = Form(""),
    session:    Session = Depends(get_session),
):
    customer = session.get(Customer, id)
    if not customer:
        return RedirectResponse("/views/customer/?error=Customer+no+encontrado", status_code=302)
    try:
        user            = customer.user
        user.name       = name
        user.email      = email
        user.country_id = int(country_id) if country_id else None
        if password:
            user.password = hasher.hash(password)
        session.add(user)

        customer.status = status == "true"
        session.add(customer)

        if balance:
            wallet = session.get(Wallet, id)
            if wallet:
                wallet.balance = Decimal(balance)
                session.add(wallet)

        session.commit()
        return RedirectResponse(f"/views/customer/{id}?success=Customer+actualizado", status_code=302)
    except Exception as e:
        session.rollback()
        customer = session.get(Customer, id)
        wallet   = session.get(Wallet, id)
        return templates.TemplateResponse(request, "customer/edit.html",
            _ctx(request, customer=customer, wallet=wallet, error=human_error(e),
                 countries=_countries(session),
                 form={"name": name, "email": email, "country_id": country_id,
                       "status": status == "true", "balance": balance}),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    customer = session.get(Customer, id)
    if not customer:
        return RedirectResponse("/views/customer/?error=Customer+no+encontrado", status_code=302)
    try:
        user = customer.user
        session.delete(customer)
        session.flush()
        if user:
            session.delete(user)
        session.commit()
        return RedirectResponse("/views/customer/?success=Customer+eliminado", status_code=302)
    except Exception as e:
        session.rollback()
        return RedirectResponse(f"/views/customer/?error={human_error(e)}", status_code=302)
