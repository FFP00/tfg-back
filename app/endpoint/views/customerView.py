from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from pwdlib import PasswordHash
from sqlalchemy import func
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.database.models.CountryModel import Country

hasher = PasswordHash.recommended()
from app.database.models.CustomerModel import Customer
from app.database.models.ImageModel import Image
from app.database.models.WalletModel import Wallet

_PAGE = 20

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error"),
        "form": {},
        **kwargs,
    }


def _get_deps(session: Session):
    return (
        session.exec(select(Country)).all(),
        session.exec(select(Image)).all(),
    )


@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Customer)
    count_q = select(func.count()).select_from(Customer)
    if search:
        cond    = (Customer.name.ilike(f"%{search}%")) | (Customer.email.ilike(f"%{search}%"))
        q       = q.where(cond)
        count_q = count_q.where(cond)
    total     = session.exec(count_q).one()
    customers = session.exec(q.offset((page - 1) * _PAGE).limit(_PAGE)).all()
    return templates.TemplateResponse(request, "customer/index.html", _ctx(request,
        customers=customers, search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    countries, images = _get_deps(session)
    return templates.TemplateResponse(request, "customer/create.html", _ctx(request, countries=countries, images=images))


@router.post("/")
def store(
    request:    Request,
    name:       str     = Form(...),
    email:      str     = Form(...),
    password:   str     = Form(...),
    status:     str     = Form("true"),
    country_id: str     = Form(""),
    image_id:   str     = Form(""),
    session:    Session = Depends(get_session),
):
    try:
        session.add(Customer(
            name=name,
            email=email,
            password=hasher.hash(password),
            status=status == "true",
            country_id=int(country_id) if country_id else None,
            image_id=int(image_id) if image_id else None,
        ))
        session.commit()
        return RedirectResponse("/views/customer/?success=Customer+creado+correctamente", status_code=302)
    except Exception as e:
        countries, images = _get_deps(session)
        return templates.TemplateResponse(request, "customer/create.html",
            _ctx(request, error=str(e), countries=countries, images=images,
                 form={"name": name, "email": email, "status": status == "true",
                       "country_id": country_id, "image_id": image_id}),
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
    countries, images = _get_deps(session)
    wallet = session.get(Wallet, id)
    return templates.TemplateResponse(request, "customer/edit.html",
        _ctx(request, customer=customer, wallet=wallet, countries=countries, images=images),
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
    image_id:   str     = Form(""),
    balance:    str     = Form(""),
    session:    Session = Depends(get_session),
):
    customer = session.get(Customer, id)
    if not customer:
        return RedirectResponse("/views/customer/?error=Customer+no+encontrado", status_code=302)
    try:
        customer.name       = name
        customer.email      = email
        if password:
            customer.password = hasher.hash(password)
        customer.status     = status == "true"
        customer.country_id = int(country_id) if country_id else None
        customer.image_id   = int(image_id)   if image_id   else None
        session.add(customer)

        if balance:
            wallet = session.get(Wallet, id)
            if wallet:
                wallet.balance = Decimal(balance)
                session.add(wallet)

        session.commit()
        return RedirectResponse(f"/views/customer/{id}?success=Customer+actualizado", status_code=302)
    except Exception as e:
        countries, images = _get_deps(session)
        wallet = session.get(Wallet, id)
        return templates.TemplateResponse(request, "customer/edit.html",
            _ctx(request, customer=customer, wallet=wallet, error=str(e), countries=countries, images=images),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    customer = session.get(Customer, id)
    if not customer:
        return RedirectResponse("/views/customer/?error=Customer+no+encontrado", status_code=302)
    try:
        session.delete(customer)
        session.commit()
        return RedirectResponse("/views/customer/?success=Customer+eliminado", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/customer/?error={e}", status_code=302)
