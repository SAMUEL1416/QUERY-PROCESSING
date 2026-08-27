"""
Authentication endpoints: register, login, logout, me, and profile
management (name/affiliation, email, password, avatar, account deletion).

Sessions are stateless JWT bearer tokens. The client stores the token and
sends it as `Authorization: Bearer <token>`. Logout simply confirms the
client should discard the token (there is no server-side session to void).
"""
import base64
import io
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

MAX_AVATAR_BYTES = 3 * 1024 * 1024  # 3MB upload cap; stored image is resized down further
AVATAR_MAX_DIMENSION = 512


@router.post("/register", response_model=schemas.TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    normalized_email = auth.normalize_email(payload.email)

    existing = db.query(models.User).filter(models.User.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = models.User(
        full_name=payload.full_name,
        email=normalized_email,
        password_hash=auth.hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    db.refresh(user)

    token = auth.create_access_token(user.id)
    return schemas.TokenOut(access_token=token, user=schemas.UserOut.model_validate(user))


@router.post("/login", response_model=schemas.TokenOut)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    normalized_email = auth.normalize_email(payload.email)
    user = db.query(models.User).filter(models.User.email == normalized_email).first()

    # Same generic message whether the email is unknown or the password is
    # wrong - never reveal which one was incorrect.
    invalid_credentials = HTTPException(status_code=401, detail="Invalid email or password.")

    if not user:
        raise invalid_credentials
    if not auth.verify_password(payload.password, user.password_hash):
        raise invalid_credentials

    token = auth.create_access_token(user.id)
    return schemas.TokenOut(access_token=token, user=schemas.UserOut.model_validate(user))


@router.post("/logout")
def logout(current_user: models.User = Depends(auth.get_current_user)):
    # Stateless JWTs: nothing to invalidate server-side. The frontend clears
    # the stored token. Requiring auth here also validates the token first.
    return {"detail": "Logged out."}


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.patch("/me", response_model=schemas.UserOut)
def update_profile(
    payload: schemas.ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    current_user.full_name = payload.full_name
    current_user.affiliation = payload.affiliation
    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/me/email", response_model=schemas.UserOut)
def update_email(
    payload: schemas.EmailUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not auth.verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")

    normalized_email = auth.normalize_email(payload.new_email)
    if normalized_email == current_user.email:
        return current_user

    existing = db.query(models.User).filter(models.User.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    current_user.email = normalized_email
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    db.refresh(current_user)
    return current_user


@router.patch("/me/password")
def update_password(
    payload: schemas.PasswordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not auth.verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    if payload.new_password != payload.confirm_new_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")
    if auth.verify_password(payload.new_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="New password must be different from the current password.")

    current_user.password_hash = auth.hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password updated successfully."}


@router.post("/me/avatar", response_model=schemas.UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")
    if len(contents) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 3MB limit.")

    try:
        from PIL import Image

        img = Image.open(io.BytesIO(contents))
        img = img.convert("RGB")
        img.thumbnail((AVATAR_MAX_DIMENSION, AVATAR_MAX_DIMENSION))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        data_uri = f"data:image/jpeg;base64,{encoded}"
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Could not process that image.") from exc

    current_user.avatar_data = data_uri
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me/avatar", response_model=schemas.UserOut)
def remove_avatar(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    current_user.avatar_data = None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me")
def delete_account(
    payload: schemas.DeleteAccountRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if not auth.verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")

    import os

    for paper in current_user.papers:
        try:
            if paper.file_path and os.path.exists(paper.file_path):
                os.remove(paper.file_path)
        except OSError:
            logger.warning("Could not remove file for paper %s during account deletion.", paper.id)

    db.delete(current_user)  # cascades to papers -> sections/features/datasets/queries
    db.commit()
    return {"detail": "Account deleted."}

