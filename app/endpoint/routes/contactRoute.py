import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.mail import send_admin_contact
from app.config.settings import settings
from app.database.models.CustomerModel import Customer
from app.database.models.DeveloperModel import Developer
from app.database.models.TokenModel import Token
from app.endpoint.schemas.contactSchema import ContactPayload, ContactResponse

router = APIRouter()

_ALGORITHM = "HS256"


def _require_sender(request: Request, session: Session) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    raw_token = auth.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(raw_token, settings.JWT_SECRET_KEY, algorithms=[_ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    if not session.exec(select(Token).where(Token.token == raw_token)).first():
        raise HTTPException(status_code=401, detail="Token revocado")
    role = payload.get("role")
    sub  = int(payload.get("sub", 0))
    if role == "customer":
        customer = session.get(Customer, sub)
        if customer and customer.status and customer.user:
            return f"{customer.user.name} (customer)"
    elif role == "developer":
        developer = session.get(Developer, sub)
        if developer and developer.status and developer.user:
            return f"{developer.user.name} (developer)"
    raise HTTPException(status_code=401, detail="Token inválido")


@router.post("/", response_model=ContactResponse, status_code=201)
def contact(
    payload: ContactPayload,
    request: Request,
    session: Session = Depends(get_session),
) -> ContactResponse:
    sender = _require_sender(request, session)
    try:
        send_admin_contact(sender, payload.textarea)
    except Exception:  # noqa: BLE001, S110
        pass
    return ContactResponse(detail="Mensaje enviado correctamente")
