from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlmodel import Session, col, or_, select

from app.config.database import get_session
from app.config.templates import templates
from app.database.models.CustomerModel import Customer
from app.database.models.FriendshipModel import Friendship

router = APIRouter()

_PAGE     = 20
_STATUSES = ("pending", "accepted", "rejected", "blocked")


def _ctx(request: Request, **kwargs):
    return {
        "request":  request,
        "success":  request.query_params.get("success"),
        "error":    request.query_params.get("error"),
        "form":     {},
        "statuses": _STATUSES,
        **kwargs,
    }


@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Friendship)
    count_q = select(func.count()).select_from(Friendship)

    if search:
        matching = session.exec(
            select(Customer.id).where(col(Customer.name).ilike(f"%{search}%"))
        ).all()
        cond    = or_(col(Friendship.customer_id_1).in_(matching), col(Friendship.customer_id_2).in_(matching))
        q       = q.where(cond)
        count_q = count_q.where(cond)

    total       = session.exec(count_q).one()
    friendships = session.exec(q.offset((page - 1) * _PAGE).limit(_PAGE)).all()

    ids = {f.customer_id_1 for f in friendships} | {f.customer_id_2 for f in friendships}
    customers = {
        c.id: c.name
        for c in session.exec(select(Customer).where(col(Customer.id).in_(ids))).all()
    } if ids else {}

    return templates.TemplateResponse(request, "friendship/index.html", _ctx(request,
        friendships=friendships, customers=customers, search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


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
    return templates.TemplateResponse(request, "friendship/edit.html", _ctx(request, friendship=friendship))


@router.post("/{id}/update")
def update(
    id:      int,
    request: Request,
    status:  str     = Form("pending"),
    session: Session = Depends(get_session),
):
    friendship = session.get(Friendship, id)
    if not friendship:
        return RedirectResponse("/views/friendship/?error=Friendship+no+encontrada", status_code=302)
    if status not in _STATUSES:
        status = "pending"
    try:
        friendship.status = status
        session.add(friendship)
        session.commit()
        return RedirectResponse(f"/views/friendship/{id}?success=Friendship+actualizada", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "friendship/edit.html",
            _ctx(request, friendship=friendship, error=str(e)),
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
