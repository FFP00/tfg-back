from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import Response
from pwdlib import PasswordHash
from redis import Redis
from sqlmodel import Session, col, select

from app.config.auth import get_current_developer, oauth2_developer
from app.config.database import get_session
from app.config.redis import get_redis
from app.database.models.CountryModel import Country
from app.database.models.DeveloperModel import Developer
from app.database.models.ImageModel import Image
from app.database.models.UserModel import User
from app.endpoint.schemas.countrySchema import CountryShow
from app.endpoint.schemas.developerSchema import (
    DeveloperImageUpload,
    LoginDeveloperResponse,
)
from app.endpoint.schemas.developerSchema import DeveloperPatch as PatchValidation
from app.endpoint.schemas.developerSchema import DeveloperPublic as PublicValidation
from app.endpoint.schemas.developerSchema import DeveloperShow as ShowValidation

hasher = PasswordHash.recommended()
router = APIRouter()

_IMAGE_FIELDS = ("profile", "banner")


def _build_public(developer: Developer) -> PublicValidation:
    u = developer.user
    return PublicValidation(
        name          = u.name if u else "",
        support_email = developer.support_email,
        website_url   = developer.website_url,
        country       = CountryShow.model_validate(u.country, from_attributes=True) if u and u.country else None,
        created_at    = developer.created_at,
        updated_at    = developer.updated_at,
    )


def _build_show(developer: Developer) -> ShowValidation:
    u = developer.user
    return ShowValidation(
        name          = u.name    if u else "",
        email         = u.email   if u else "",
        support_email = developer.support_email,
        website_url   = developer.website_url,
        status        = developer.status,
        country       = CountryShow.model_validate(u.country, from_attributes=True) if u and u.country else None,
        created_at    = developer.created_at,
        updated_at    = developer.updated_at,
    )


def _developer_by_name(name: str, session: Session) -> Developer:
    user      = session.exec(select(User).where(User.name == name)).first()
    developer = session.get(Developer, user.id) if user else None
    if not developer or not developer.status:
        raise HTTPException(status_code=404, detail="Developer no encontrado")
    return developer


# ── Static routes first (before /{name}) ─────────────────────────────────────


@router.get("/me", response_model=LoginDeveloperResponse)
def me(
    token:   str       = Depends(oauth2_developer),
    current: Developer = Depends(get_current_developer),
) -> LoginDeveloperResponse:
    return LoginDeveloperResponse(
        access_token = token,
        developer    = _build_show(current),
    )


@router.get("/", response_model=list[PublicValidation])
def index(search: str = "", session: Session = Depends(get_session)) -> list[PublicValidation]:
    q = select(Developer).join(User, Developer.user_id == User.id).where(Developer.status)
    if search:
        q = q.where(col(User.name).ilike(f"%{search}%"))
    return [_build_public(d) for d in session.exec(q).all()]


@router.patch("/me", response_model=ShowValidation)
def update_me(
    payload: PatchValidation,
    current: Developer = Depends(get_current_developer),
    session: Session   = Depends(get_session),
) -> ShowValidation:
    data = payload.model_dump(exclude_unset=True)
    user = current.user

    if "name" in data and session.exec(
        select(User).where(User.name == data["name"], User.id != user.id)
    ).first():
        raise HTTPException(status_code=409, detail="Nombre ya en uso")

    if "email" in data and session.exec(
        select(User).where(User.email == data["email"], User.id != user.id)
    ).first():
        raise HTTPException(status_code=409, detail="Email ya en uso")

    if "support_email" in data and session.exec(
        select(Developer).where(
            Developer.support_email == data["support_email"],
            Developer.user_id != current.user_id,
        )
    ).first():
        raise HTTPException(status_code=409, detail="Support email ya en uso")

    if "website_url" in data and data["website_url"] and session.exec(
        select(Developer).where(
            Developer.website_url == data["website_url"],
            Developer.user_id != current.user_id,
        )
    ).first():
        raise HTTPException(status_code=409, detail="Website URL ya en uso")

    if "country_code" in data:
        country = session.exec(select(Country).where(Country.code == data.pop("country_code"))).first()
        if not country:
            raise HTTPException(status_code=404, detail="Country no encontrado")
        user.country_id = country.id

    if "password" in data:
        user.password = hasher.hash(data.pop("password"))

    user_fields = {k: data.pop(k) for k in ("name", "email") if k in data}
    dev_fields  = dict(data.items())

    if user_fields:
        user.sqlmodel_update(user_fields)

    session.add(user)

    if dev_fields:
        current.sqlmodel_update(dev_fields)
        session.add(current)

    session.commit()
    session.refresh(current)
    return _build_show(current)


@router.patch("/me/image", status_code=204)
async def upload_image(
    body:    Annotated[DeveloperImageUpload, Form()],
    current: Developer = Depends(get_current_developer),
    session: Session   = Depends(get_session),
    redis:   Redis     = Depends(get_redis),
) -> Response:
    if not body.profile and not body.banner:
        raise HTTPException(status_code=400, detail="Se requiere al menos un campo: profile o banner")
    image = session.get(Image, current.user_id)
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    name = current.user.name if current.user else ""
    if body.profile:
        image.profile = await body.profile.read()
    if body.banner:
        image.banner = await body.banner.read()
    session.add(image)
    session.commit()
    if body.profile:
        redis.delete(f"img:developer:{name}:profile")
    if body.banner:
        redis.delete(f"img:developer:{name}:banner")
    return Response(status_code=204)


# ── Dynamic routes ────────────────────────────────────────────────────────────


@router.get("/{name}/image/{field}")
def get_image(
    name: str, field: str,
    session: Session = Depends(get_session),
    redis:   Redis   = Depends(get_redis),
) -> Response:
    if field not in _IMAGE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Campo inválido. Válidos: {list(_IMAGE_FIELDS)}")
    cache_key = f"img:developer:{name}:{field}"
    if cached := redis.get(cache_key):
        return Response(content=cached, media_type="image/jpeg")
    developer = _developer_by_name(name, session)
    image     = session.get(Image, developer.user_id)
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    data: bytes | None = getattr(image, field, None)
    if not data:
        raise HTTPException(status_code=404, detail=f"Campo '{field}' vacío")
    redis.set(cache_key, data, ex=604800)
    return Response(content=data, media_type="image/jpeg")


@router.get("/{name}", response_model=PublicValidation)
def show(name: str, session: Session = Depends(get_session)) -> PublicValidation:
    return _build_public(_developer_by_name(name, session))
