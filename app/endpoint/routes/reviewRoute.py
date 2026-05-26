from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.ReviewModel import Review
from app.endpoint.schemas.reviewSchema import ReviewCreate as CreateValidation
from app.endpoint.schemas.reviewSchema import ReviewPatch as PatchValidation
from app.endpoint.schemas.reviewSchema import ReviewShow as ShowValidation

router = APIRouter()

@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    review = Review.model_validate(payload)
    session.add(review)
    session.commit()
    session.refresh(review)
    return review



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    reviews = session.exec(select(Review)).all()
    return reviews



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    review = session.exec(select(Review).where(Review.id == id)).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review with specified ID doesn't exist")
    return review



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    review = session.exec(select(Review).where(Review.id == id)).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review with specified ID doesn't exist")

    review.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(review)
    session.commit()
    session.refresh(review)
    return review



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    review = session.exec(select(Review).where(Review.id == id)).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review with specified ID doesn't exist")

    session.delete(review)
    session.commit()

    return {"status": "ok"}
