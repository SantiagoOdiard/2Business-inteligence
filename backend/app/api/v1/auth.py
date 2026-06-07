from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import current_user
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_password, hash_token, verify_password
from app.data.schemas import ChangePasswordRequest, LoginRequest, PasswordRequest, RefreshRequest, ResetPasswordRequest, TokenResponse, UserProfile
from app.domain.models import PasswordReset, Permission, RolePermission, Session as UserSession, User
from app.infrastructure.database import get_db
from app.services.audit_service import audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _permissions(db: Session, user: User) -> list[str]:
    return [
        row[0]
        for row in db.query(Permission.action)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id == user.role_id)
        .all()
    ]


def _issue_tokens(db: Session, user: User, request: Request, device: str) -> TokenResponse:
    permissions = _permissions(db, user)
    access = create_access_token(str(user.id), user.role.name, permissions)
    refresh = create_refresh_token()
    db.add(
        UserSession(
            user_id=user.id,
            refresh_token_hash=hash_token(refresh),
            device=device,
            ip_address=request.client.host if request.client else "unknown",
            expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_days),
        )
    )
    db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.username).first()
    ip = request.client.host if request.client else "unknown"
    if not user:
        audit(db, "Login", "Failed", ip, f"Unknown email {payload.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.locked_until and user.locked_until > datetime.utcnow():
        audit(db, "Login", "Locked", ip, user.email, user.id)
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account temporarily locked")
    if not verify_password(payload.password, user.hashed_password):
        user.failed_logins += 1
        if user.failed_logins >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)
        db.commit()
        audit(db, "Login", "Failed", ip, user.email, user.id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user.failed_logins = 0
    user.locked_until = None
    db.commit()
    audit(db, "Login", "Success", ip, payload.device, user.id)
    return _issue_tokens(db, user, request, payload.device)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    token_hash = hash_token(payload.refresh_token)
    session = db.query(UserSession).filter(UserSession.refresh_token_hash == token_hash, UserSession.revoked_at == None).first()
    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user = db.get(User, session.user_id)
    session.revoked_at = datetime.utcnow()
    db.commit()
    return _issue_tokens(db, user, request, payload.device)


@router.post("/logout")
def logout(payload: RefreshRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    session = db.query(UserSession).filter(UserSession.refresh_token_hash == hash_token(payload.refresh_token)).first()
    if session:
        session.revoked_at = datetime.utcnow()
        db.commit()
    audit(db, "Logout", "Success", request.client.host if request.client else "unknown", payload.device, user.id)
    return {"status": "logged_out"}


@router.post("/forgot-password")
def forgot_password(payload: PasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        token = create_refresh_token()
        db.add(PasswordReset(user_id=user.id, token_hash=hash_token(token), expires_at=datetime.utcnow() + timedelta(hours=1)))
        db.commit()
        return {"status": "created", "reset_token_for_demo": token}
    return {"status": "created"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    item = db.query(PasswordReset).filter(PasswordReset.token_hash == hash_token(payload.token), PasswordReset.used_at == None).first()
    if not item or item.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.get(User, item.user_id)
    user.hashed_password = hash_password(payload.new_password)
    item.used_at = datetime.utcnow()
    db.commit()
    return {"status": "password_reset"}


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password does not match")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"status": "password_changed"}


@router.get("/me", response_model=UserProfile)
def me(user: User = Depends(current_user)):
    return UserProfile(id=user.id, email=user.email, full_name=user.full_name, role=user.role.name, department=user.department.name)
