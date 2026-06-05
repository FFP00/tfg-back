from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlmodel import Session, col, or_, select

from app.config.database import get_session
from app.config.templates import templates
from app.database.models.CustomerModel import Customer
from app.database.models.FriendshipModel import Friendship
from app.database.models.UserModel import User

router = APIRouter()

_PAGE     = 20
_STATUSES = ("pending", "accepted")


def _ctx(request: Request, **kwargs):
    return {
        "request":  request,
        "success":  request.query_params.get("success"),
        "error":    request.query_params.get("error"),
        "form":     {},
        "statuses": _STATUSES,
        **kwargs,
    }


def _names_map(friendship_list: list[Friendship], session: Session) -> dict[int, str]:
    ids = set()
    for f in friendship_list:
        ids.update([f.customer_user_id_1, f.customer_user_id_2, f.initiator_id])
    if not ids:
        return {}
    customers = session.exec(select(Customer).where(col(Customer.user_id).in_(ids))).all()
    return {c.user_id: c.user.name if c.user else f"#{c.user_id}" for c in customers}


@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Friendship)
    count_q = select(func.count()).select_from(Friendship)

    if search:
        matching = session.exec(
            select(User.id).where(col(User.name).ilike(f"%{search}%"), User.type == "CUS")
        ).all()
        cond    = or_(
            col(Friendship.customer_user_id_1).in_(matching),
            col(Friendship.customer_user_id_2).in_(matching),
        )
        q       = q.where(cond)
        count_q = count_q.where(cond)

    total       = session.exec(count_q).one()
    friendships = session.exec(
        q.order_by(Friendship.created_at.desc()).offset((page - 1) * _PAGE).limit(_PAGE)
    ).all()
    names = _names_map(friendships, session)

    return templates.TemplateResponse(request, "friendship/index.html", _ctx(request,
        friendships=friendships, names=names, search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    friendship = session.get(Friendship, id)
    if not friendship:
        return RedirectResponse("/views/friendship/?error=Amistad+no+encontrada", status_code=302)
    names = _names_map([friendship], session)
    return templates.TemplateResponse(request, "friendship/show.html", _ctx(request, friendship=friendship, names=names))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    friendship = session.get(Friendship, id)
    if not friendship:
        return RedirectResponse("/views/friendship/?error=Amistad+no+encontrada", status_code=302)
    names = _names_map([friendship], session)
    return templates.TemplateResponse(request, "friendship/edit.html", _ctx(request, friendship=friendship, names=names))


@router.post("/{id}/update")
def update(
    id:      int,
    request: Request,
    status:  str     = Form("pending"),
    session: Session = Depends(get_session),
):
    friendship = session.get(Friendship, id)
    if not friendship:
        return RedirectResponse("/views/friendship/?error=Amistad+no+encontrada", status_code=302)
    if status not in _STATUSES:
        status = "pending"
    try:
        friendship.status = status
        session.add(friendship)
        session.commit()
        return RedirectResponse(f"/views/friendship/{id}?success=Amistad+actualizada", status_code=302)
    except Exception as e:
        session.rollback()
        friendship = session.get(Friendship, id)
        names      = _names_map([friendship], session) if friendship else {}
        return templates.TemplateResponse(request, "friendship/edit.html",
            _ctx(request, friendship=friendship, names=names, error=str(e)),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    friendship = session.get(Friendship, id)
    if not friendship:
        return RedirectResponse("/views/friendship/?error=Amistad+no+encontrada", status_code=302)
    try:
        session.delete(friendship)
        session.commit()
        return RedirectResponse("/views/friendship/?success=Amistad+eliminada", status_code=302)
    except Exception as e:
        session.rollback()
        return RedirectResponse(f"/views/friendship/?error={str(e)}", status_code=302)
