from collections.abc import Iterator
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.config.auth import get_current_customer, get_current_developer
from app.config.database import get_session
from app.config.mail import send_admin_review_pending, send_admin_title_pending
from app.database.models.CustomerModel import Customer
from app.database.models.CustomerTitleModel import CustomerTitle
from app.database.models.DeveloperModel import Developer
from app.database.models.GenreModel import Genre
from app.database.models.GenreTitleModel import GenreTitle
from app.database.models.MediaModel import Media
from app.database.models.ReviewModel import Review
from app.database.models.TitleModel import Title
from app.database.models.UserModel import User
from app.endpoint.schemas.countrySchema import CountryShow
from app.endpoint.schemas.developerSchema import DeveloperPublic
from app.endpoint.schemas.titleSchema import (
    ReviewCreate,
    ReviewPatch,
    ReviewShow,
    TitleCard,
    TitleMediaUpload,
    VoteResponse,
)
from app.endpoint.schemas.titleSchema import TitleCreate as CreateValidation
from app.endpoint.schemas.titleSchema import TitlePatch as PatchValidation
from app.endpoint.schemas.titleSchema import TitleShow as ShowValidation

router = APIRouter()

_IMAGE_FIELDS = ("capsule", "header", "store_1", "store_2", "store_3", "store_4", "store_5", "store_6")
_CHUNK        = 1024 * 256


def _stream_range(data: bytes, start: int, end: int) -> Iterator[bytes]:
    pos = start
    while pos <= end:
        chunk_end = min(pos + _CHUNK - 1, end)
        yield data[pos : chunk_end + 1]
        pos = chunk_end + 1


def _genres_for(title_id: int, session: Session) -> list[Genre]:
    links  = session.exec(select(GenreTitle).where(GenreTitle.title_id == title_id)).all()
    result = []
    for link in links:
        g = session.get(Genre, link.genre_id)
        if g:
            result.append(g)
    return result


def _customer_price(title: Title) -> Decimal:
    if title.actual_discount == 0:
        return title.release_price
    return (title.release_price * (1 - Decimal(title.actual_discount) / 100)).quantize(Decimal("0.01"))


def _build_developer_public(developer: Developer) -> DeveloperPublic:
    u = developer.user
    return DeveloperPublic(
        name          = u.name if u else "",
        support_email = developer.support_email,
        website_url   = developer.website_url,
        country       = CountryShow.model_validate(u.country, from_attributes=True) if u and u.country else None,
        created_at    = developer.created_at,
        updated_at    = developer.updated_at,
    )


def _to_card(title: Title, session: Session) -> TitleCard:
    title_id = title.id or 0
    genres   = _genres_for(title_id, session)
    dev_name = title.developer.user.name if title.developer and title.developer.user else None
    return TitleCard(
        name            = title.name,
        release_price   = _customer_price(title),
        actual_discount = title.actual_discount,
        genres          = [{"name": g.name} for g in genres],
        developer_name  = dev_name,
    )


def _to_show(title: Title, session: Session, *, customer: bool = False) -> ShowValidation:
    title_id  = title.id or 0
    genres    = _genres_for(title_id, session)
    developer = _build_developer_public(title.developer) if title.developer else None
    return ShowValidation(
        name            = title.name,
        status          = title.status,
        actual_discount = title.actual_discount,
        release_date    = title.release_date,
        release_price   = _customer_price(title) if customer else title.release_price,
        genres          = [{"name": g.name} for g in genres],
        developer       = developer,
        created_at      = title.created_at,
        updated_at      = title.updated_at,
    )


# ── Static routes first ───────────────────────────────────────────────────────


@router.get("/random", response_model=TitleCard)
def random_title(session: Session = Depends(get_session)) -> TitleCard:
    title = session.exec(select(Title).where(Title.status).order_by(func.random()).limit(1)).first()
    if not title:
        raise HTTPException(status_code=404, detail="No hay títulos disponibles")
    return _to_card(title, session)


@router.get("/me", response_model=list[ShowValidation])
def my_titles(
    current: Developer = Depends(get_current_developer),
    session: Session   = Depends(get_session),
) -> list[ShowValidation]:
    titles = session.exec(select(Title).where(Title.developer_user_id == current.user_id)).all()
    return [_to_show(t, session) for t in titles]


@router.get("/", response_model=list[TitleCard])
def index(
    search:    str     = "",
    genre:     str     = "",
    developer: str     = "",
    session:   Session = Depends(get_session),
) -> list[TitleCard]:
    q = select(Title).where(Title.status)
    if search:
        q = q.where(col(Title.name).ilike(f"%{search}%"))
    if developer:
        user = session.exec(select(User).where(User.name == developer)).first()
        dev  = session.get(Developer, user.id) if user else None
        if not dev:
            return []
        q = q.where(Title.developer_user_id == dev.user_id)
    if genre:
        g = session.exec(select(Genre).where(Genre.name == genre)).first()
        if not g:
            return []
        q = q.where(col(Title.id).in_(select(GenreTitle.title_id).where(GenreTitle.genre_id == g.id)))
    return [_to_card(t, session) for t in session.exec(q).all()]


@router.post("/", response_model=ShowValidation, status_code=201)
def create(
    payload: CreateValidation,
    current: Developer = Depends(get_current_developer),
    session: Session   = Depends(get_session),
) -> ShowValidation:
    title = Title(
        name              = payload.name,
        release_date      = payload.release_date,
        release_price     = payload.release_price,
        actual_discount   = payload.actual_discount,
        developer_user_id = current.user_id,
        status            = False,
    )
    session.add(title)
    session.commit()
    session.refresh(title)
    try:
        dev_name = current.user.name if current.user else str(current.user_id)
        send_admin_title_pending(payload.name, dev_name)
    except Exception:  # noqa: BLE001, S110
        pass
    return _to_show(title, session)


# ── Dynamic routes ────────────────────────────────────────────────────────────


@router.patch("/{name}/media", status_code=204)
async def patch_media(
    name:    str,
    body:    Annotated[TitleMediaUpload, Form()],
    current: Developer = Depends(get_current_developer),
    session: Session   = Depends(get_session),
) -> Response:
    title = session.exec(
        select(Title).where(Title.name == name, Title.developer_user_id == current.user_id)
    ).first()
    if not title:
        raise HTTPException(status_code=404, detail="Título no encontrado o no eres el propietario")
    media = session.exec(select(Media).where(Media.title_id == title.id)).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media no encontrada")
    uploads = {
        "capsule": body.capsule, "header": body.header,
        "store_1": body.store_1, "store_2": body.store_2, "store_3": body.store_3,
        "store_4": body.store_4, "store_5": body.store_5, "store_6": body.store_6,
        "trailer": body.trailer,
    }
    if not any(uploads.values()):
        raise HTTPException(status_code=400, detail="Se requiere al menos un campo")
    for field, upload in uploads.items():
        if upload:
            setattr(media, field, await upload.read())
    session.add(media)
    session.commit()
    return Response(status_code=204)


@router.get("/{name}/media/{field}")
def get_media(
    name: str, field: str, request: Request, session: Session = Depends(get_session)
) -> Response:
    if field not in (*_IMAGE_FIELDS, "trailer"):
        raise HTTPException(status_code=400, detail=f"Campo inválido. Válidos: {[*_IMAGE_FIELDS, 'trailer']}")
    title = session.exec(select(Title).where(Title.name == name, Title.status)).first()
    if not title:
        raise HTTPException(status_code=404, detail="Título no encontrado")
    media = session.exec(select(Media).where(Media.title_id == title.id)).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media no encontrada")
    data: bytes | None = getattr(media, field, None)
    if not data:
        raise HTTPException(status_code=404, detail=f"Campo '{field}' vacío")

    if field != "trailer":
        return Response(content=data, media_type="image/jpeg")

    total        = len(data)
    range_header = request.headers.get("range")

    if not range_header:
        return StreamingResponse(
            _stream_range(data, 0, total - 1),
            media_type="video/mp4",
            headers={"Content-Length": str(total), "Accept-Ranges": "bytes"},
        )

    try:
        range_val        = range_header.replace("bytes=", "")
        start_str, end_str = range_val.split("-")
        start = int(start_str)
        end   = int(end_str) if end_str else total - 1
    except ValueError as exc:
        raise HTTPException(status_code=416, detail="Range header inválido") from exc

    if start >= total or end >= total or start > end:
        raise HTTPException(
            status_code=416,
            detail="Range Not Satisfiable",
            headers={"Content-Range": f"bytes */{total}"},
        )

    return StreamingResponse(
        _stream_range(data, start, end),
        status_code=206,
        media_type="video/mp4",
        headers={
            "Content-Range":  f"bytes {start}-{end}/{total}",
            "Content-Length": str(end - start + 1),
            "Accept-Ranges":  "bytes",
        },
    )


@router.get("/{name}/reviews", response_model=list[ReviewShow])
def get_reviews(name: str, session: Session = Depends(get_session)) -> list[ReviewShow]:
    title = session.exec(select(Title).where(Title.name == name, Title.status)).first()
    if not title:
        raise HTTPException(status_code=404, detail="Título no encontrado")
    cts    = session.exec(select(CustomerTitle).where(CustomerTitle.title_id == title.id)).all()
    result = []
    for ct in cts:
        review = session.exec(
            select(Review).where(Review.customer_title_id == ct.id, Review.status == True)  # noqa: E712
        ).first()
        if review:
            customer = session.get(Customer, ct.customer_user_id)
            result.append(ReviewShow(
                content       = review.content,
                recommends    = review.recommends,
                votes         = review.votes,
                customer_name = customer.user.name if customer and customer.user else "",
                title_name    = title.name,
                created_at    = review.created_at,
            ))
    return result


@router.post("/{name}/reviews", response_model=ReviewShow, status_code=201)
def create_review(
    name:    str,
    payload: ReviewCreate,
    current: Customer = Depends(get_current_customer),
    session: Session  = Depends(get_session),
) -> ReviewShow:
    title = session.exec(select(Title).where(Title.name == name, Title.status)).first()
    if not title:
        raise HTTPException(status_code=404, detail="Título no encontrado")
    ct = session.exec(
        select(CustomerTitle).where(
            CustomerTitle.title_id == title.id,
            CustomerTitle.customer_user_id == current.user_id,
        )
    ).first()
    if not ct:
        raise HTTPException(status_code=403, detail="Debes tener el juego para reseñarlo")
    if session.exec(select(Review).where(Review.customer_title_id == ct.id)).first():
        raise HTTPException(status_code=409, detail="Ya tienes una reseña para este juego")
    review = Review(
        content           = payload.content,
        recommends        = payload.recommends,
        votes             = 0,
        customer_title_id = ct.id,
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    try:
        cname = current.user.name if current.user else str(current.user_id)
        send_admin_review_pending(cname, title.name)
    except Exception:  # noqa: BLE001, S110
        pass
    return ReviewShow(
        content       = review.content,
        recommends    = review.recommends,
        votes         = review.votes,
        customer_name = current.user.name if current.user else "",
        title_name    = title.name,
        created_at    = review.created_at,
    )


@router.patch("/{name}/reviews/me", response_model=ReviewShow)
def update_review(
    name:    str,
    payload: ReviewPatch,
    current: Customer = Depends(get_current_customer),
    session: Session  = Depends(get_session),
) -> ReviewShow:
    title = session.exec(select(Title).where(Title.name == name, Title.status)).first()
    if not title:
        raise HTTPException(status_code=404, detail="Título no encontrado")
    ct = session.exec(
        select(CustomerTitle).where(
            CustomerTitle.title_id == title.id,
            CustomerTitle.customer_user_id == current.user_id,
        )
    ).first()
    if not ct:
        raise HTTPException(status_code=403, detail="No tienes este juego")
    review = session.exec(select(Review).where(Review.customer_title_id == ct.id)).first()
    if not review:
        raise HTTPException(status_code=404, detail="No tienes reseña para este juego")
    review.sqlmodel_update(payload.model_dump(exclude_unset=True))
    session.add(review)
    session.commit()
    session.refresh(review)
    return ReviewShow(
        content       = review.content,
        recommends    = review.recommends,
        votes         = review.votes,
        customer_name = current.user.name if current.user else "",
        title_name    = title.name,
        created_at    = review.created_at,
    )


@router.post("/{name}/reviews/{customer_name}/vote", response_model=VoteResponse)
def vote_review(
    name:          str,
    customer_name: str,
    current:       Customer = Depends(get_current_customer),
    session:       Session  = Depends(get_session),
) -> VoteResponse:
    title = session.exec(select(Title).where(Title.name == name, Title.status)).first()
    if not title:
        raise HTTPException(status_code=404, detail="Título no encontrado")
    author_user = session.exec(select(User).where(User.name == customer_name)).first()
    author      = session.get(Customer, author_user.id) if author_user else None
    if not author or not author.status:
        raise HTTPException(status_code=404, detail="Autor de la reseña no encontrado")
    if author.user_id == current.user_id:
        raise HTTPException(status_code=400, detail="No puedes votar tu propia reseña")
    ct = session.exec(
        select(CustomerTitle).where(
            CustomerTitle.title_id == title.id,
            CustomerTitle.customer_user_id == author.user_id,
        )
    ).first()
    if not ct:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    review = session.exec(select(Review).where(Review.customer_title_id == ct.id)).first()
    if not review:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    review.votes = (review.votes or 0) + 1
    session.add(review)
    session.commit()
    return VoteResponse(votes=review.votes)


@router.patch("/{name}", response_model=ShowValidation)
def update(
    name:    str,
    payload: PatchValidation,
    current: Developer = Depends(get_current_developer),
    session: Session   = Depends(get_session),
) -> ShowValidation:
    title = session.exec(
        select(Title).where(Title.name == name, Title.developer_user_id == current.user_id)
    ).first()
    if not title:
        raise HTTPException(status_code=404, detail="Título no encontrado o no eres el propietario")

    data = payload.model_dump(exclude_unset=True)

    if "genres" in data:
        genre_names: list[str] = data.pop("genres")
        for link in session.exec(select(GenreTitle).where(GenreTitle.title_id == title.id)).all():
            session.delete(link)
        for gname in genre_names:
            genre = session.exec(select(Genre).where(Genre.name == gname)).first()
            if not genre:
                raise HTTPException(status_code=404, detail=f"Genre '{gname}' no encontrado")
            session.add(GenreTitle(title_id=title.id, genre_id=genre.id))

    if data:
        title.sqlmodel_update(data)
    session.add(title)
    session.commit()
    session.refresh(title)
    return _to_show(title, session)


@router.get("/{name}", response_model=ShowValidation)
def show(name: str, session: Session = Depends(get_session)) -> ShowValidation:
    title = session.exec(select(Title).where(Title.name == name, Title.status)).first()
    if not title:
        raise HTTPException(status_code=404, detail="Título no encontrado")
    return _to_show(title, session, customer=True)
