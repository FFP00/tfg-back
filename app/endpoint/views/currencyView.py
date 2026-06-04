from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.config.database import get_session
from app.config.errors import human_error
from app.config.templates import templates
from app.database.models.CurrencyModel import Currency

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


@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Currency)
    count_q = select(func.count()).select_from(Currency)
    if search:
        cond    = (
            col(Currency.name).ilike(f"%{search}%")
            | col(Currency.code).ilike(f"%{search}%")
            | col(Currency.symbol).ilike(f"%{search}%")
        )
        q       = q.where(cond)
        count_q = count_q.where(cond)
    total      = session.exec(count_q).one()
    currencies = session.exec(q.order_by(Currency.created_at.desc()).offset((page - 1) * _PAGE).limit(_PAGE)).all()
    return templates.TemplateResponse(request, "currency/index.html", _ctx(request,
        currencies=currencies, search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/create")
def create(request: Request):
    return templates.TemplateResponse(request, "currency/create.html", _ctx(request))


@router.post("/")
def store(
    request: Request,
    name:    str     = Form(...),
    code:    str     = Form(...),
    symbol:  str     = Form(...),
    session: Session = Depends(get_session),
):
    try:
        session.add(Currency(name=name, code=code, symbol=symbol))
        session.commit()
        return RedirectResponse("/views/currency/?success=Moneda+creada+correctamente", status_code=302)
    except Exception as e:
        session.rollback()
        return templates.TemplateResponse(request, "currency/create.html",
            _ctx(request, error=human_error(e), form={"name": name, "code": code, "symbol": symbol}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    currency = session.get(Currency, id)
    if not currency:
        return RedirectResponse("/views/currency/?error=Moneda+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "currency/show.html", _ctx(request, currency=currency))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    currency = session.get(Currency, id)
    if not currency:
        return RedirectResponse("/views/currency/?error=Moneda+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "currency/edit.html", _ctx(request, currency=currency))


@router.post("/{id}/update")
def update(
    id:      int,
    request: Request,
    name:    str     = Form(...),
    code:    str     = Form(...),
    symbol:  str     = Form(...),
    session: Session = Depends(get_session),
):
    currency = session.get(Currency, id)
    if not currency:
        return RedirectResponse("/views/currency/?error=Moneda+no+encontrada", status_code=302)
    try:
        currency.name   = name
        currency.code   = code
        currency.symbol = symbol
        session.add(currency)
        session.commit()
        return RedirectResponse(f"/views/currency/{id}?success=Moneda+actualizada", status_code=302)
    except Exception as e:
        session.rollback()
        currency = session.get(Currency, id)
        return templates.TemplateResponse(request, "currency/edit.html",
            _ctx(request, currency=currency, error=human_error(e),
                 form={"name": name, "code": code, "symbol": symbol}),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    currency = session.get(Currency, id)
    if not currency:
        return RedirectResponse("/views/currency/?error=Moneda+no+encontrada", status_code=302)
    try:
        session.delete(currency)
        session.commit()
        return RedirectResponse("/views/currency/?success=Moneda+eliminada", status_code=302)
    except Exception as e:
        session.rollback()
        return RedirectResponse(f"/views/currency/?error={human_error(e)}", status_code=302)
