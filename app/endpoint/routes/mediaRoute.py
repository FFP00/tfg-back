from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.endpoint.models.MediaModel import Media
from app.endpoint.schemas.mediaSchema import MediaCreate as CreateValidation
from app.endpoint.schemas.mediaSchema import MediaPatch as PatchValidation
from app.endpoint.schemas.mediaSchema import MediaShow as ShowValidation

router = APIRouter()

_IMAGE_FIELDS = ("capsule", "header", "store_1", "store_2", "store_3", "store_4", "store_5", "store_6")
_CHUNK = 1024 * 256  # 256 KB chunks


def _stream_range(data: bytes, start: int, end: int):
    pos = start
    while pos <= end:
        chunk_end = min(pos + _CHUNK - 1, end)
        yield data[pos : chunk_end + 1]
        pos = chunk_end + 1


@router.post("/", response_model=ShowValidation, status_code=201)
def create(payload: CreateValidation, session: Session = Depends(get_session)):
    media = Media.model_validate(payload)
    session.add(media)
    session.commit()
    session.refresh(media)
    return media



@router.get("/", response_model=list[ShowValidation], status_code=200)
def index(session: Session = Depends(get_session)):
    medias = session.exec(select(Media)).all()
    return medias



@router.get("/{id}", response_model=ShowValidation, status_code=200)
def show_by_id(id: int, session: Session = Depends(get_session)):
    media = session.exec(select(Media).where(Media.id == id)).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media with specified ID doesn't exist")
    return media



@router.get("/{id}/image/{field}", status_code=200)
def get_image(id: int, field: str, session: Session = Depends(get_session)):
    if field not in _IMAGE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid image field. Valid: {list(_IMAGE_FIELDS)}")

    media = session.exec(select(Media).where(Media.id == id)).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media with specified ID doesn't exist")

    data: bytes | None = getattr(media, field)
    if not data:
        raise HTTPException(status_code=404, detail=f"Field '{field}' is empty for this media")

    return Response(content=data, media_type="image/jpeg")



@router.get("/{id}/trailer", status_code=200)
def get_trailer(id: int, request: Request, session: Session = Depends(get_session)):
    media = session.exec(select(Media).where(Media.id == id)).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media with specified ID doesn't exist")

    if not media.trailer:
        raise HTTPException(status_code=404, detail="This media has no trailer")

    data   = media.trailer
    total  = len(data)
    range_header = request.headers.get("range")

    if not range_header:
        return StreamingResponse(
            _stream_range(data, 0, total - 1),
            media_type="video/mp4",
            headers={"Content-Length": str(total), "Accept-Ranges": "bytes"},
        )

    # Parse Range: bytes=start-end
    try:
        range_val = range_header.replace("bytes=", "")
        start_str, end_str = range_val.split("-")
        start = int(start_str)
        end   = int(end_str) if end_str else total - 1
    except ValueError as exc:
        raise HTTPException(status_code=416, detail="Invalid Range header") from exc

    if start >= total or end >= total or start > end:
        raise HTTPException(
            status_code=416,
            detail="Range Not Satisfiable",
            headers={"Content-Range": f"bytes */{total}"},
        )

    chunk_size = end - start + 1

    return StreamingResponse(
        _stream_range(data, start, end),
        status_code=206,
        media_type="video/mp4",
        headers={
            "Content-Range":  f"bytes {start}-{end}/{total}",
            "Content-Length": str(chunk_size),
            "Accept-Ranges":  "bytes",
        },
    )



@router.patch("/{id}", response_model=ShowValidation)
def update(id: int, payload: PatchValidation, session: Session = Depends(get_session)):
    media = session.exec(select(Media).where(Media.id == id)).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media with specified ID doesn't exist")

    media.sqlmodel_update(payload.model_dump(exclude_unset=True))

    session.add(media)
    session.commit()
    session.refresh(media)
    return media



@router.delete("/{id}")
def delete(id: int, session: Session = Depends(get_session)):
    media = session.exec(select(Media).where(Media.id == id)).first()

    if not media:
        raise HTTPException(status_code=404, detail="Media with specified ID doesn't exist")

    session.delete(media)
    session.commit()

    return {"status": "ok"}
