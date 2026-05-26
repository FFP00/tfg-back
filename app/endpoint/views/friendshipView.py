from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.CustomerModel import Customer
from app.endpoint.models.FriendshipModel import Friendship

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error"),
        "form": {},
        **kwargs,
    }


def _get_customers(session: Session):
    return session.exec(select(Customer)).all()


@router.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    friendships = session.exec(select(Friendship)).all()
    return templates.TemplateResponse(request, "friendship/index.html", _ctx(request, friendships=friendships))


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(request, "friendship/create.html", _ctx(request, customers=_get_customers(session))
    )


@router.post("/")
def store(
    request: Request,
    customer_id_1: str = Form(...),
    customer_id_2: str = Form(...),
    status: str = Form("false"),
    session: Session = Depends(get_session),
):
    try:
        session.add(Friendship(
            customer_id_1=int(customer_id_1),
            customer_id_2=int(customer_id_2),
            status=status == "true",
        ))
        session.commit()
        return RedirectResponse("/views/friendship/?success=Friendship+creada+correctamente", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "friendship/create.html",
            _ctx(request, error=str(e), customers=_get_customers(session),
                 form={"customer_id_1": customer_id_1, "customer_id_2": customer_id_2,
                       "status": status == "true"}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    friendship = session.get(Friendship, id)
    if not friendship:
        return RedirectResponse("/views/friendship/?error=Friendship+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "friendship/show.html", _ctx(request, friendship=friendship))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    friendship = session.get(Friendship, id)
    if not friendship:
        return RedirectResponse("/views/friendship/?error=Friendship+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "friendship/edit.html", _ctx(request, friendship=friendship, customers=_get_customers(session))
    )


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    customer_id_1: str = Form(...),
    customer_id_2: str = Form(...),
    status: str = Form("false"),
    session: Session = Depends(get_session),
):
    friendship = session.get(Friendship, id)
    if not friendship:
        return RedirectResponse("/views/friendship/?error=Friendship+no+encontrada", status_code=302)
    try:
        friendship.customer_id_1 = int(customer_id_1)
        friendship.customer_id_2 = int(customer_id_2)
        friendship.status = status == "true"
        session.add(friendship)
        session.commit()
        return RedirectResponse(f"/views/friendship/{id}?success=Friendship+actualizada", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "friendship/edit.html",
            _ctx(request, friendship=friendship, error=str(e), customers=_get_customers(session)),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    friendship = session.get(Friendship, id)
    if not friendship:
        return RedirectResponse("/views/friendship/?error=Friendship+no+encontrada", status_code=302)
    try:
        session.delete(friendship)
        session.commit()
        return RedirectResponse("/views/friendship/?success=Friendship+eliminada", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/friendship/?error={e}", status_code=302)
