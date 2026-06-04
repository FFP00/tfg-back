from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.config.database import get_session
from app.config.errors import human_error
from app.config.templates import templates
from app.database.models.CountryModel import Country
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


def _currencies(session: Session):
    return session.exec(select(Currency).order_by(Currency.name)).all()


@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Country)
    count_q = select(func.count()).select_from(Country)
    if search:
        cond    = (
            col(Country.native_name).ilike(f"%{search}%")
            | col(Country.english_name).ilike(f"%{search}%")
            | col(Country.code).ilike(f"%{search}%")
        )
        q       = q.where(cond)
        count_q = count_q.where(cond)
    total     = session.exec(count_q).one()
    countries = session.exec(q.order_by(Country.created_at.desc()).offset((page - 1) * _PAGE).limit(_PAGE)).all()
    return templates.TemplateResponse(request, "country/index.html", _ctx(request,
        countries=countries, search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(request, "country/create.html", _ctx(request, currencies=_currencies(session)))


@router.post("/")
def store(
    request:      Request,
    native_name:  str     = Form(...),
    english_name: str     = Form(...),
    code:         str     = Form(...),
    currency_id:  str     = Form(""),
    session:      Session = Depends(get_session),
):
    try:
        session.add(Country(
            native_name  = native_name,
            english_name = english_name,
            code         = code,
            currency_id  = int(currency_id) if currency_id else None,
        ))
        session.commit()
        return RedirectResponse("/views/country/?success=País+creado+correctamente", status_code=302)
    except Exception as e:
        session.rollback()
        return templates.TemplateResponse(request, "country/create.html",
            _ctx(request, error=human_error(e), currencies=_currencies(session),
                 form={"native_name": native_name, "english_name": english_name,
                       "code": code, "currency_id": currency_id}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    country = session.get(Country, id)
    if not country:
        return RedirectResponse("/views/country/?error=País+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "country/show.html", _ctx(request, country=country))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    country = session.get(Country, id)
    if not country:
        return RedirectResponse("/views/country/?error=País+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "country/edit.html",
        _ctx(request, country=country, currencies=_currencies(session)),
    )


@router.post("/{id}/update")
def update(
    id:           int,
    request:      Request,
    native_name:  str     = Form(...),
    english_name: str     = Form(...),
    code:         str     = Form(...),
    currency_id:  str     = Form(""),
    session:      Session = Depends(get_session),
):
    country = session.get(Country, id)
    if not country:
        return RedirectResponse("/views/country/?error=País+no+encontrado", status_code=302)
    try:
        country.native_name  = native_name
        country.english_name = english_name
        country.code         = code
        country.currency_id  = int(currency_id) if currency_id else None
        session.add(country)
        session.commit()
        return RedirectResponse(f"/views/country/{id}?success=País+actualizado", status_code=302)
    except Exception as e:
        session.rollback()
        country = session.get(Country, id)
        return templates.TemplateResponse(request, "country/edit.html",
            _ctx(request, country=country, error=human_error(e), currencies=_currencies(session),
                 form={"native_name": native_name, "english_name": english_name,
                       "code": code, "currency_id": currency_id}),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    country = session.get(Country, id)
    if not country:
        return RedirectResponse("/views/country/?error=País+no+encontrado", status_code=302)
    try:
        session.delete(country)
        session.commit()
        return RedirectResponse("/views/country/?success=País+eliminado", status_code=302)
    except Exception as e:
        session.rollback()
        return RedirectResponse(f"/views/country/?error={human_error(e)}", status_code=302)
