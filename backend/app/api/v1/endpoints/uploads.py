"""Upload endpoints — multipart file → preview → confirm."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin_or_faculty
from app.models.user import User
from app.repositories.upload_repo import upload_repo
from app.schemas.upload import UploadConfirmIn, UploadConfirmResult, UploadOut, UploadPreview
from app.services import upload_service
from app.services.auth_service import write_audit
from app.utils.files import validate_size_and_save


router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=UploadPreview, dependencies=[Depends(require_admin_or_faculty)])
def upload_and_preview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
) -> UploadPreview:
    disk_path, size, ext, original = validate_size_and_save(file)
    upload = upload_service.register_upload(
        db, disk_path=disk_path, original_name=original, size_bytes=size, ext=ext, user_id=me.id
    )
    try:
        preview = upload_service.preview_upload(db, upload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Failed to parse: {exc}") from exc
    write_audit(db, user_id=me.id, action="upload.preview", entity="upload", entity_id=upload.id, meta={"size": size})
    return UploadPreview(**preview)


@router.post(
    "/{upload_id}/confirm",
    response_model=UploadConfirmResult,
    dependencies=[Depends(require_admin_or_faculty)],
)
def confirm_upload(
    upload_id: int,
    payload: UploadConfirmIn,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
) -> UploadConfirmResult:
    upload = upload_repo.get(db, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    res = upload_service.confirm_upload(db, upload, payload.mapping, payload.skip_invalid)
    write_audit(db, user_id=me.id, action="upload.confirm", entity="upload", entity_id=upload.id, meta=res)
    return UploadConfirmResult(**res)


@router.get("", response_model=list[UploadOut])
def list_uploads(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[UploadOut]:
    return [UploadOut.model_validate(u) for u in upload_service.list_uploads(db)]
