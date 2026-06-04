from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlmodel import Session, or_, select

from app.config.auth import get_current_customer
from app.config.database import get_session
from app.database.models.CustomerModel import Customer
from app.database.models.FriendshipModel import Friendship
from app.database.models.UserModel import User
from app.endpoint.schemas.friendshipSchema import FriendshipPatch as PatchValidation
from app.endpoint.schemas.friendshipSchema import FriendshipShow as ShowValidation

router = APIRouter()


def _customer_by_name(name: str, session: Session) -> Customer:
    user     = session.exec(select(User).where(User.name == name)).first()
    customer = session.get(Customer, user.id) if user else None
    if not customer or not customer.status:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return customer


def _get_friendship(id1: int, id2: int, session: Session) -> Friendship | None:
    lo, hi = min(id1, id2), max(id1, id2)
    return session.exec(
        select(Friendship).where(
            Friendship.customer_user_id_1 == lo,
            Friendship.customer_user_id_2 == hi,
        )
    ).first()


# ── Static routes first (before /{name}) ─────────────────────────────────────


@router.get("/pending", response_model=list[ShowValidation])
def pending(
    current: Customer = Depends(get_current_customer),
    session: Session  = Depends(get_session),
) -> list[ShowValidation]:
    friendships = session.exec(
        select(Friendship).where(
            or_(
                Friendship.customer_user_id_1 == current.user_id,
                Friendship.customer_user_id_2 == current.user_id,
            ),
            Friendship.initiator_id != current.user_id,
            Friendship.status == "pending",
        )
    ).all()
    result = []
    for f in friendships:
        sender = session.get(Customer, f.initiator_id)
        result.append(ShowValidation(
            status     = f.status,
            from_name  = sender.user.name if sender and sender.user else None,
            created_at = f.created_at,
        ))
    return result


# ── Dynamic routes ────────────────────────────────────────────────────────────


@router.post("/{name}", response_model=ShowValidation, status_code=201)
def send_request(
    name:    str,
    current: Customer = Depends(get_current_customer),
    session: Session  = Depends(get_session),
) -> ShowValidation:
    if current.user and name == current.user.name:
        raise HTTPException(status_code=400, detail="No puedes enviarte una solicitud a ti mismo")
    target = _customer_by_name(name, session)
    if _get_friendship(current.user_id, target.user_id, session):
        raise HTTPException(status_code=409, detail="Ya existe una relación con este usuario")
    lo, hi = min(current.user_id, target.user_id), max(current.user_id, target.user_id)
    friendship = Friendship(
        customer_user_id_1 = lo,
        customer_user_id_2 = hi,
        initiator_id       = current.user_id,
    )
    session.add(friendship)
    session.commit()
    session.refresh(friendship)
    return ShowValidation(
        status     = friendship.status,
        from_name  = current.user.name if current.user else None,
        created_at = friendship.created_at,
    )


@router.patch("/{name}", response_model=ShowValidation)
def respond_request(
    name:    str,
    payload: PatchValidation,
    current: Customer = Depends(get_current_customer),
    session: Session  = Depends(get_session),
) -> ShowValidation:
    target     = _customer_by_name(name, session)
    friendship = _get_friendship(current.user_id, target.user_id, session)
    if not friendship:
        raise HTTPException(status_code=404, detail="Solicitud de amistad no encontrada")
    if friendship.initiator_id == current.user_id:
        raise HTTPException(status_code=403, detail="Solo el receptor puede aceptar la solicitud")
    if friendship.status != "pending":
        raise HTTPException(status_code=409, detail="La solicitud ya fue procesada")
    friendship.status = payload.status
    session.add(friendship)
    session.commit()
    session.refresh(friendship)
    return ShowValidation(
        status     = friendship.status,
        from_name  = target.user.name if target.user else None,
        created_at = friendship.created_at,
    )


@router.delete("/{name}", status_code=204)
def remove(
    name:    str,
    current: Customer = Depends(get_current_customer),
    session: Session  = Depends(get_session),
) -> Response:
    target     = _customer_by_name(name, session)
    friendship = _get_friendship(current.user_id, target.user_id, session)
    if not friendship:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    session.delete(friendship)
    session.commit()
    return Response(status_code=204)
