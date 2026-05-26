from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.CustomerModel import Customer
from app.endpoint.models.CustomerTitleModel import CustomerTitle
from app.endpoint.models.TitleModel import Title

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
        session.exec(select(Customer)).all(),
        session.exec(select(Title)).all(),
    )


@router.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    customer_titles = session.exec(select(CustomerTitle)).all()
    return templates.TemplateResponse(request, "customer_title/index.html", _ctx(request, customer_titles=customer_titles)
    )


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    customers, titles = _get_deps(session)
    return templates.TemplateResponse(request, "customer_title/create.html", _ctx(request, customers=customers, titles=titles)
    )


@router.post("/")
def store(
    request: Request,
    customer_id: str = Form(...),
    title_id: str = Form(...),
    playtime: int = Form(0),
    session: Session = Depends(get_session),
):
    try:
        session.add(CustomerTitle(
            customer_id=int(customer_id),
            title_id=int(title_id),
            playtime=playtime,
        ))
        session.commit()
        return RedirectResponse(
            "/views/customer_title/?success=Customer-Title+creado+correctamente", status_code=302
        )
    except Exception as e:
        customers, titles = _get_deps(session)
        return templates.TemplateResponse(request, "customer_title/create.html",
            _ctx(request, error=str(e), customers=customers, titles=titles,
                 form={"customer_id": customer_id, "title_id": title_id, "playtime": playtime}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    customer_title = session.get(CustomerTitle, id)
    if not customer_title:
        return RedirectResponse("/views/customer_title/?error=Customer-Title+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "customer_title/show.html", _ctx(request, customer_title=customer_title)
    )


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    customer_title = session.get(CustomerTitle, id)
    if not customer_title:
        return RedirectResponse("/views/customer_title/?error=Customer-Title+no+encontrado", status_code=302)
    customers, titles = _get_deps(session)
    return templates.TemplateResponse(request, "customer_title/edit.html",
        _ctx(request, customer_title=customer_title, customers=customers, titles=titles),
    )


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    customer_id: str = Form(...),
    title_id: str = Form(...),
    playtime: int = Form(0),
    session: Session = Depends(get_session),
):
    customer_title = session.get(CustomerTitle, id)
    if not customer_title:
        return RedirectResponse("/views/customer_title/?error=Customer-Title+no+encontrado", status_code=302)
    try:
        customer_title.customer_id = int(customer_id)
        customer_title.title_id = int(title_id)
        customer_title.playtime = playtime
        session.add(customer_title)
        session.commit()
        return RedirectResponse(
            f"/views/customer_title/{id}?success=Customer-Title+actualizado", status_code=302
        )
    except Exception as e:
        customers, titles = _get_deps(session)
        return templates.TemplateResponse(request, "customer_title/edit.html",
            _ctx(request, customer_title=customer_title, error=str(e),
                 customers=customers, titles=titles),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    customer_title = session.get(CustomerTitle, id)
    if not customer_title:
        return RedirectResponse("/views/customer_title/?error=Customer-Title+no+encontrado", status_code=302)
    try:
        session.delete(customer_title)
        session.commit()
        return RedirectResponse("/views/customer_title/?success=Customer-Title+eliminado", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/customer_title/?error={e}", status_code=302)
