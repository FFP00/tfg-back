from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.CustomerModel import Customer
from app.endpoint.models.WalletModel import Wallet

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error"),
        "form": {},
        **kwargs,
    }


@router.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    wallets = session.exec(select(Wallet)).all()
    return templates.TemplateResponse(request, "wallet/index.html", _ctx(request, wallets=wallets))


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    customers = session.exec(select(Customer)).all()
    return templates.TemplateResponse(request, "wallet/create.html", _ctx(request, customers=customers))


@router.post("/")
def store(
    request: Request,
    customer_id: str = Form(...),
    balance: str = Form("0"),
    session: Session = Depends(get_session),
):
    try:
        session.add(Wallet(
            customer_id=int(customer_id),
            balance=Decimal(balance),
        ))
        session.commit()
        return RedirectResponse("/views/wallet/?success=Wallet+creada+correctamente", status_code=302)
    except Exception as e:
        customers = session.exec(select(Customer)).all()
        return templates.TemplateResponse(request, "wallet/create.html",
            _ctx(request, error=str(e), customers=customers,
                 form={"customer_id": customer_id, "balance": balance}),
        )


@router.get("/{customer_id}")
def show(customer_id: int, request: Request, session: Session = Depends(get_session)):
    wallet = session.get(Wallet, customer_id)
    if not wallet:
        return RedirectResponse("/views/wallet/?error=Wallet+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "wallet/show.html", _ctx(request, wallet=wallet))


@router.get("/{customer_id}/edit")
def edit(customer_id: int, request: Request, session: Session = Depends(get_session)):
    wallet = session.get(Wallet, customer_id)
    if not wallet:
        return RedirectResponse("/views/wallet/?error=Wallet+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "wallet/edit.html", _ctx(request, wallet=wallet))


@router.post("/{customer_id}/update")
def update(
    customer_id: int,
    request: Request,
    balance: str = Form(...),
    session: Session = Depends(get_session),
):
    wallet = session.get(Wallet, customer_id)
    if not wallet:
        return RedirectResponse("/views/wallet/?error=Wallet+no+encontrada", status_code=302)
    try:
        wallet.balance = Decimal(balance)
        session.add(wallet)
        session.commit()
        return RedirectResponse(f"/views/wallet/{customer_id}?success=Wallet+actualizada", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "wallet/edit.html",
            _ctx(request, wallet=wallet, error=str(e)),
        )


@router.post("/{customer_id}/delete")
def delete(customer_id: int, session: Session = Depends(get_session)):
    wallet = session.get(Wallet, customer_id)
    if not wallet:
        return RedirectResponse("/views/wallet/?error=Wallet+no+encontrada", status_code=302)
    try:
        session.delete(wallet)
        session.commit()
        return RedirectResponse("/views/wallet/?success=Wallet+eliminada", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/wallet/?error={e}", status_code=302)
