import uuid
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .. import models, schemas, storage
from ..database import get_db
from ..image_processing import InvalidImageError, process_image
from ..security import require_admin_session, require_admin_origin

router = APIRouter(prefix="/images", tags=["images"])
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_IMAGES = 10
SECTION_KEYS = {"ABOUT", "STORY", "GOALS", "OUTSIDE_WORK"}


def _asset_url(image_id: str) -> str:
    return f"/images/{image_id}/file"


def _asset_out(asset: models.ImageAsset) -> schemas.ImageAssetOut:
    return schemas.ImageAssetOut(
        id=asset.id,
        slot=asset.slot,
        original_filename=asset.original_filename,
        content_type=asset.content_type,
        size_bytes=asset.size_bytes,
        width=asset.width,
        height=asset.height,
        uploaded_at=asset.uploaded_at,
        url=_asset_url(asset.id),
    )


@router.get("", response_model=list[schemas.ImageAssetOut])
def list_images(db: Session = Depends(get_db)):
    assets = db.scalars(select(models.ImageAsset).order_by(models.ImageAsset.slot)).all()
    return [_asset_out(asset) for asset in assets]


@router.get("/{image_id}/file")
def get_image_file(image_id: str, db: Session = Depends(get_db)):
    asset = db.get(models.ImageAsset, image_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Image not found")
    try:
        image_bytes = storage.download_file(asset.object_key)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to retrieve the image from storage") from exc
    filename = quote(Path(asset.original_filename).name[:160])
    return StreamingResponse(
        BytesIO(image_bytes),
        media_type="image/webp",
        headers={
            "Content-Disposition": f'inline; filename="{image_id}.webp"; filename*=UTF-8\'\'{filename}',
            "Cache-Control": "public, max-age=3600",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("", response_model=schemas.ImageAssetOut, status_code=201,
             dependencies=[Depends(require_admin_session), Depends(require_admin_origin)])
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 8 MB or smaller.")
    try:
        processed, width, height = process_image(data)
    except InvalidImageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Serialize slot allocation so concurrent uploads cannot exceed ten assets.
    db.execute(text("SELECT pg_advisory_xact_lock(734821906)"))
    used_slots = set(db.scalars(select(models.ImageAsset.slot)).all())
    slot = next((candidate for candidate in range(1, MAX_IMAGES + 1) if candidate not in used_slots), None)
    if slot is None:
        db.rollback()
        raise HTTPException(status_code=409, detail="The image library is full (10 images maximum).")

    image_id = str(uuid.uuid4())
    object_key = f"portfolio-images/{image_id}.webp"
    try:
        storage.upload_image(processed, object_key)
        asset = models.ImageAsset(
            id=image_id,
            slot=slot,
            object_key=object_key,
            original_filename=Path((file.filename or "image").replace("\\", "/")).name[:180] or "image",
            content_type="image/webp",
            size_bytes=len(processed),
            width=width,
            height=height,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return _asset_out(asset)
    except Exception:
        db.rollback()
        storage.delete_file(object_key)
        raise


@router.put("/{image_id}", response_model=schemas.ImageAssetOut,
            dependencies=[Depends(require_admin_session), Depends(require_admin_origin)])
async def replace_image(image_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    asset = db.get(models.ImageAsset, image_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Image not found")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 8 MB or smaller.")
    try:
        processed, width, height = process_image(data)
    except InvalidImageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    new_key = f"portfolio-images/{uuid.uuid4().hex}.webp"
    old_key = asset.object_key
    try:
        storage.upload_image(processed, new_key)
        asset.object_key = new_key
        asset.original_filename = Path((file.filename or "image").replace("\\", "/")).name[:180] or "image"
        asset.content_type = "image/webp"
        asset.size_bytes = len(processed)
        asset.width = width
        asset.height = height
        db.commit()
        db.refresh(asset)
    except Exception:
        db.rollback()
        storage.delete_file(new_key)
        raise
    storage.delete_file(old_key)
    return _asset_out(asset)


@router.delete("/{image_id}", status_code=204,
               dependencies=[Depends(require_admin_session)])
def delete_image(image_id: str, db: Session = Depends(get_db)):
    asset = db.get(models.ImageAsset, image_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Image not found")
    old_key = asset.object_key
    assignments = db.scalars(
        select(models.BioImageAssignment).where(models.BioImageAssignment.image_id == image_id)
    ).all()
    for assignment in assignments:
        db.delete(assignment)
    db.delete(asset)
    db.commit()
    storage.delete_file(old_key)


@router.get("/assignments", response_model=list[schemas.BioImageAssignmentOut])
def get_bio_image_assignments(db: Session = Depends(get_db)):
    assignments = db.scalars(select(models.BioImageAssignment)).all()
    return [
        schemas.BioImageAssignmentOut(
            section_key=item.section_key,
            image_id=item.image_id,
            url=_asset_url(item.image_id),
        )
        for item in assignments
    ]


@router.put("/assignments/{section_key}", response_model=schemas.BioImageAssignmentOut | None,
            dependencies=[Depends(require_admin_session)])
def set_bio_image_assignment(
    section_key: str,
    payload: schemas.BioImageAssignmentUpdate,
    db: Session = Depends(get_db),
):
    key = section_key.upper()
    if key not in SECTION_KEYS:
        raise HTTPException(status_code=400, detail="Unknown About-page image position.")
    current = db.get(models.BioImageAssignment, key)
    if payload.image_id is None:
        if current:
            db.delete(current)
            db.commit()
        return None
    if not db.get(models.ImageAsset, payload.image_id):
        raise HTTPException(status_code=404, detail="Selected image does not exist.")
    if current:
        current.image_id = payload.image_id
    else:
        current = models.BioImageAssignment(section_key=key, image_id=payload.image_id)
        db.add(current)
    db.commit()
    return schemas.BioImageAssignmentOut(
        section_key=key,
        image_id=payload.image_id,
        url=_asset_url(payload.image_id),
    )
