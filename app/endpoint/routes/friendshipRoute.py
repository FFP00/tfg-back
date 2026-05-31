from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlmodel import Session, or_, select

from app.config.auth import get_current_customer
from app.config.database import get_session
from app.database.models.CustomerModel import Customer
from app.database.models.FriendshipModel import Friendship
from app.endpoint.schemas.friendshipSchema import FriendshipPatch, FriendshipShow

router = APIRouter()


# ── Static routes first (before /{name}) ─────────────────────────────────────


@router.get("/pending", response_model=list[FriendshipShow])
def pending(
    current: Customer = Depends(get_current_customer),
    session: Session = Depends(get_session),
) -> list[FriendshipShow]:
    friendships = session.exec(
        select(Friendship).where(
            Friendship.customer_id_2 == current.id,
            Friendship.status == "pending",
        )
    ).all()
    result = []
    for f in friendships:
        sender = session.get(Customer, f.customer_id_1)
        result.append(
            FriendshipShow(
                status=f.status,
                from_name=sender.name if sender else None,
                created_at=f.created_at,
            )
        )
    return result


# ── Dynamic routes ────────────────────────────────────────────────────────────


@router.post("/{name}", response_model=FriendshipShow, status_code=201)
def send_request(
    name: str,
    current: Customer = Depends(get_current_customer),
    session: Session = Depends(get_session),
) -> FriendshipShow:
    if name == current.name:
        raise HTTPException(
            status_code=400, detail="No puedes enviarte una solicitud a ti mismo"
        )
    target = session.exec(
        select(Customer).where(Customer.name == name, Customer.status)
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    existing = session.exec(
        select(Friendship).where(
            or_(
                (Friendship.customer_id_1 == current.id)
                & (Friendship.customer_id_2 == target.id),
                (Friendship.customer_id_1 == target.id)
                & (Friendship.customer_id_2 == current.id),
            )
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="Ya existe una relación con este usuario"
        )
    friendship = Friendship(
        customer_id_1=current.id,
        customer_id_2=target.id,
        status="pending",
    )
    session.add(friendship)
    session.commit()
    session.refresh(friendship)
    return FriendshipShow(
        status=friendship.status,
        from_name=current.name,
        created_at=friendship.created_at,
    )


@router.patch("/{name}", response_model=FriendshipShow)
def respond_request(
    name: str,
    payload: FriendshipPatch,
    current: Customer = Depends(get_current_customer),
    session: Session = Depends(get_session),
) -> FriendshipShow:
    target = session.exec(
        select(Customer).where(Customer.name == name, Customer.status)
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if payload.status in ("accepted", "rejected"):
        # Solo el receptor puede aceptar o rechazar
        friendship = session.exec(
            select(Friendship).where(
                Friendship.customer_id_1 == target.id,
                Friendship.customer_id_2 == current.id,
            )
        ).first()
    else:
        # Cualquiera de los dos puede bloquear
        friendship = session.exec(
            select(Friendship).where(
                or_(
                    (Friendship.customer_id_1 == target.id)
                    & (Friendship.customer_id_2 == current.id),
                    (Friendship.customer_id_1 == current.id)
                    & (Friendship.customer_id_2 == target.id),
                )
            )
        ).first()

    if not friendship:
        raise HTTPException(
            status_code=404, detail="Solicitud de amistad no encontrada"
        )

    if payload.status == "rejected":
        session.delete(friendship)
        session.commit()
        return FriendshipShow(status="rejected", from_name=target.name)

    friendship.status = payload.status
    session.add(friendship)
    session.commit()
    session.refresh(friendship)
    return FriendshipShow(
        status=friendship.status,
        from_name=target.name,
        created_at=friendship.created_at,
    )


@router.delete("/{name}", status_code=204)
def remove(
    name: str,
    current: Customer = Depends(get_current_customer),
    session: Session = Depends(get_session),
) -> Response:
    target = session.exec(
        select(Customer).where(Customer.name == name, Customer.status)
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    friendship = session.exec(
        select(Friendship).where(
            or_(
                (Friendship.customer_id_1 == current.id)
                & (Friendship.customer_id_2 == target.id),
                (Friendship.customer_id_1 == target.id)
                & (Friendship.customer_id_2 == current.id),
            )
        )
    ).first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Relación no encontrada")
    session.delete(friendship)
    session.commit()
    return Response(status_code=204)
