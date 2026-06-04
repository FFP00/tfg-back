from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.config.database import get_session
from app.config.errors import human_error
from app.config.templates import templates
from app.database.models.CustomerModel import Customer
from app.database.models.CustomerTitleModel import CustomerTitle
from app.database.models.ReviewModel import Review
from app.database.models.TitleModel import Title
from app.database.models.UserModel import User

_PAGE = 20

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error":   request.query_params.get("error"),
        "form":    {},
        **kwargs,
    }


def _enrich(reviews: list[Review], session: Session) -> list[dict]:
    result = []
    for r in reviews:
        ct       = session.get(CustomerTitle, r.customer_title_id) if r.customer_title_id else None
        title    = session.get(Title, ct.title_id) if ct else None
        customer = session.get(Customer, ct.customer_user_id) if ct else None
        result.append({
            "review":        r,
            "title_name":    title.name if title else "—",
            "customer_name": customer.user.name if customer and customer.user else "—",
        })
    return result


@router.get("/")
def index(request: Request, search: str = "", game: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Review)
    count_q = select(func.count()).select_from(Review)

    filters = []

    if search:
        matching_users = session.exec(
            select(Customer.user_id)
            .join(User, Customer.user_id == User.id)
            .where(col(User.name).ilike(f"%{search}%"))
        ).all()
        matching_cts = session.exec(
            select(CustomerTitle.id)
            .where(col(CustomerTitle.customer_user_id).in_(matching_users))
        ).all()
        filters.append(col(Review.customer_title_id).in_(matching_cts))

    if game:
        matching_titles = session.exec(
            select(Title.id).where(col(Title.name).ilike(f"%{game}%"))
        ).all()
        matching_cts_game = session.exec(
            select(CustomerTitle.id)
            .where(col(CustomerTitle.title_id).in_(matching_titles))
        ).all()
        filters.append(col(Review.customer_title_id).in_(matching_cts_game))

    for f in filters:
        q       = q.where(f)
        count_q = count_q.where(f)

    total   = session.exec(count_q).one()
    reviews = session.exec(q.order_by(Review.created_at.desc()).offset((page - 1) * _PAGE).limit(_PAGE)).all()
    rows    = _enrich(reviews, session)

    return templates.TemplateResponse(request, "review/index.html", _ctx(request,
        rows=rows, search=search, game=game, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    review = session.get(Review, id)
    if not review:
        return RedirectResponse("/views/review/?error=Review+no+encontrada", status_code=302)
    enriched = _enrich([review], session)
    return templates.TemplateResponse(request, "review/show.html", _ctx(request,
        review=review, row=enriched[0],
    ))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    review = session.get(Review, id)
    if not review:
        return RedirectResponse("/views/review/?error=Review+no+encontrada", status_code=302)
    enriched = _enrich([review], session)
    return templates.TemplateResponse(request, "review/edit.html",
        _ctx(request, review=review, row=enriched[0]),
    )


@router.post("/{id}/update")
def update(
    id:         int,
    request:    Request,
    content:    str     = Form(...),
    recommends: str     = Form("true"),
    status:     str     = Form("false"),
    session:    Session = Depends(get_session),
):
    review = session.get(Review, id)
    if not review:
        return RedirectResponse("/views/review/?error=Review+no+encontrada", status_code=302)
    try:
        review.content    = content
        review.recommends = recommends == "true"
        review.status     = status == "true"
        session.add(review)
        session.commit()
        return RedirectResponse(f"/views/review/{id}?success=Review+actualizada", status_code=302)
    except Exception as e:
        session.rollback()
        review   = session.get(Review, id)
        enriched = _enrich([review], session) if review else [{"review": None, "title_name": "—", "customer_name": "—"}]
        return templates.TemplateResponse(request, "review/edit.html",
            _ctx(request, review=review, row=enriched[0], error=human_error(e),
                 form={"content": content, "recommends": recommends == "true", "status": status == "true"}),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    review = session.get(Review, id)
    if not review:
        return RedirectResponse("/views/review/?error=Review+no+encontrada", status_code=302)
    try:
        session.delete(review)
        session.commit()
        return RedirectResponse("/views/review/?success=Review+eliminada", status_code=302)
    except Exception as e:
        session.rollback()
        return RedirectResponse(f"/views/review/?error={human_error(e)}", status_code=302)
