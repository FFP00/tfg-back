from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.CustomerTitleModel import CustomerTitle
from app.endpoint.models.ReviewModel import Review

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error"),
        "form": {},
        **kwargs,
    }


def _get_customer_titles(session: Session):
    return session.exec(select(CustomerTitle)).all()


@router.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    reviews = session.exec(select(Review)).all()
    return templates.TemplateResponse(request, "review/index.html", _ctx(request, reviews=reviews))


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(request, "review/create.html", _ctx(request, customer_titles=_get_customer_titles(session))
    )


@router.post("/")
def store(
    request: Request,
    content: str = Form(...),
    votes: int = Form(0),
    recommends: str = Form("true"),
    status: str = Form("false"),
    customer_title_id: str = Form(""),
    session: Session = Depends(get_session),
):
    try:
        session.add(Review(
            content=content,
            votes=votes,
            recommends=recommends == "true",
            status=status == "true",
            customer_title_id=int(customer_title_id) if customer_title_id else None,
        ))
        session.commit()
        return RedirectResponse("/views/review/?success=Review+creada+correctamente", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "review/create.html",
            _ctx(request, error=str(e), customer_titles=_get_customer_titles(session),
                 form={"content": content, "votes": votes, "recommends": recommends == "true",
                       "status": status == "true", "customer_title_id": customer_title_id}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    review = session.get(Review, id)
    if not review:
        return RedirectResponse("/views/review/?error=Review+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "review/show.html", _ctx(request, review=review))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    review = session.get(Review, id)
    if not review:
        return RedirectResponse("/views/review/?error=Review+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "review/edit.html",
        _ctx(request, review=review, customer_titles=_get_customer_titles(session)),
    )


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    content: str = Form(...),
    votes: int = Form(0),
    recommends: str = Form("true"),
    status: str = Form("false"),
    customer_title_id: str = Form(""),
    session: Session = Depends(get_session),
):
    review = session.get(Review, id)
    if not review:
        return RedirectResponse("/views/review/?error=Review+no+encontrada", status_code=302)
    try:
        review.content = content
        review.votes = votes
        review.recommends = recommends == "true"
        review.status = status == "true"
        review.customer_title_id = int(customer_title_id) if customer_title_id else None
        session.add(review)
        session.commit()
        return RedirectResponse(f"/views/review/{id}?success=Review+actualizada", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "review/edit.html",
            _ctx(request, review=review, error=str(e),
                 customer_titles=_get_customer_titles(session)),
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
        return RedirectResponse(f"/views/review/?error={e}", status_code=302)
