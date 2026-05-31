from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.database.models.TokenModel import Token

router = APIRouter()

_PAGE = 20


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error":   request.query_params.get("error"),
        **kwargs,
    }


@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Token)
    count_q = select(func.count()).select_from(Token)
    if search:
        cond    = Token.token.ilike(f"%{search}%")
        q       = q.where(cond)
        count_q = count_q.where(cond)
    total  = session.exec(count_q).one()
    tokens = session.exec(q.offset((page - 1) * _PAGE).limit(_PAGE)).all()
    return templates.TemplateResponse(request, "token/index.html", _ctx(request,
        tokens=tokens, search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    token = session.get(Token, id)
    if not token:
        return RedirectResponse("/views/token/?error=Token+no+encontrado", status_code=302)
    try:
        session.delete(token)
        session.commit()
        return RedirectResponse("/views/token/?success=Token+revocado", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/token/?error={e}", status_code=302)
