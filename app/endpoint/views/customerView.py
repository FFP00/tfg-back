from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.CountryModel import Country
from app.endpoint.models.CustomerModel import Customer
from app.endpoint.models.ImageModel import Image

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
def index(request: Request, search: str = "", session: Session = Depends(get_session)):
    q = select(Customer)
    if search:
        q = q.where(
            (Customer.name.ilike(f"%{search}%")) | (Customer.email.ilike(f"%{search}%"))
        )
    customers = session.exec(q).all()
    return templates.TemplateResponse(request, "customer/index.html", _ctx(request, customers=customers, search=search)
    )


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    countries, images = _get_deps(session)
    return templates.TemplateResponse(request, "customer/create.html", _ctx(request, countries=countries, images=images)
    )


@router.post("/")
def store(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    status: str = Form("true"),
    country_id: str = Form(""),
    image_id: str = Form(""),
    session: Session = Depends(get_session),
):
    try:
        session.add(Customer(
            name=name,
            email=email,
            password=password,
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
    return templates.TemplateResponse(request, "customer/show.html", _ctx(request, customer=customer))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    customer = session.get(Customer, id)
    if not customer:
        return RedirectResponse("/views/customer/?error=Customer+no+encontrado", status_code=302)
    countries, images = _get_deps(session)
    return templates.TemplateResponse(request, "customer/edit.html", _ctx(request, customer=customer, countries=countries, images=images)
    )


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(""),
    status: str = Form("true"),
    country_id: str = Form(""),
    image_id: str = Form(""),
    session: Session = Depends(get_session),
):
    customer = session.get(Customer, id)
    if not customer:
        return RedirectResponse("/views/customer/?error=Customer+no+encontrado", status_code=302)
    try:
        customer.name = name
        customer.email = email
        if password:
            customer.password = password
        customer.status = status == "true"
        customer.country_id = int(country_id) if country_id else None
        customer.image_id = int(image_id) if image_id else None
        session.add(customer)
        session.commit()
        return RedirectResponse(f"/views/customer/{id}?success=Customer+actualizado", status_code=302)
    except Exception as e:
        countries, images = _get_deps(session)
        return templates.TemplateResponse(request, "customer/edit.html",
            _ctx(request, customer=customer, error=str(e), countries=countries, images=images),
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
