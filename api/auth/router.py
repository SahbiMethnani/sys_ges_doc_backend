import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.auth.dependencies import get_current_user
from api.auth.email_service import send_password_reset_email, smtp_is_configured
from api.auth.ldap_service import (
    LDAPError,
    authenticate_ldap,
    change_ldap_password,
    register_ldap_user,
)
from api.auth.security import (
    create_access_token,
    generate_refresh_token,
    generate_password_reset_token,
    hash_password_reset_token,
    hash_refresh_token,
    password_reset_token_expires_at,
    refresh_token_expires_at,
)
from api.auth.user_service import (
    create_user_from_registration,
    get_user_by_username,
    get_valid_refresh_token,
    revoke_refresh_token,
    store_refresh_token,
    sync_user_after_ldap_login,
)
from api.db.models import PasswordResetToken, RefreshToken, User
from api.db.session import get_db
from api.models import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from config import JWT_ACCESS_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentification"])
logger = logging.getLogger(__name__)


def _build_token_response(db: Session, user: User) -> TokenResponse:
    access = create_access_token(
        user_id=user.id,
        username=user.ldap_uid,
        role=user.role,
    )
    refresh_plain = generate_refresh_token()
    store_refresh_token(
        db,
        user.id,
        hash_refresh_token(refresh_plain),
        refresh_token_expires_at(),
    )
    return TokenResponse(
        access_token=access,
        token_type="Bearer",
        expires_in=JWT_ACCESS_EXPIRE_MINUTES * 60,
        refresh_token=refresh_plain,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Connexion via LDAP ; le profil (rôle) est lu depuis MySQL."""
    ldap_info = authenticate_ldap(body.username, body.password)
    if ldap_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects.",
        )

    user = sync_user_after_ldap_login(db, ldap_info)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé.",
        )
    return _build_token_response(db, user)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    
    try:
        ldap_info = register_ldap_user(
            body.username,
            body.password,
            display_name=body.display_name,
            email=body.email,
        )
        user = create_user_from_registration(db, ldap_info)
        return UserResponse(
            id=user.id,
            username=user.ldap_uid,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
        )
    except LDAPError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post("/forgot-password", response_model=MessageResponse, status_code=202)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    print("DEBUG endpoint appelé, username =", repr(body.username))
    user = get_user_by_username(db, body.username.strip())
    print("DEBUG user:", user, "| email:", getattr(user, "email", None), "| smtp:", smtp_is_configured())
    generic_message = (
        "Si le compte existe et que l'envoi d'e-mail est configuré, "
        "un lien de réinitialisation va être envoyé."
    )
    user = get_user_by_username(db, body.username.strip())
    if user is None or not user.email or not smtp_is_configured():
        return MessageResponse(message=generic_message)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    recent_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.created_at > now - timedelta(seconds=60),
        )
        .first()
    )
    if recent_token is not None:
        return MessageResponse(message=generic_message)

    raw_token = generate_password_reset_token()
    reset_row = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_password_reset_token(raw_token),
        expires_at=password_reset_token_expires_at().replace(tzinfo=None),
    )
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).delete(synchronize_session=False)
    db.add(reset_row)
    db.commit()

    try:
        send_password_reset_email(user.email, raw_token)
    except Exception:
        logger.exception("Échec d'envoi du lien de réinitialisation.")
        #db.delete(reset_row)
        #db.commit()

    return MessageResponse(message=generic_message)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    reset_row = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == hash_password_reset_token(body.token),
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .with_for_update()
        .first()
    )
    if reset_row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lien invalide, expiré ou déjà utilisé.",
        )

    user = db.query(User).filter(User.id == reset_row.user_id).first()
    if user is None or not user.ldap_dn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lien invalide, expiré ou déjà utilisé.",
        )

    try:
        change_ldap_password(user.ldap_dn, body.new_password)
    except LDAPError as e:
        logger.exception("Échec de modification du mot de passe LDAP.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Impossible de modifier le mot de passe pour le moment.",
        ) from e

    reset_row.used_at = now
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None),
    ).update({RefreshToken.revoked_at: now}, synchronize_session=False)
    db.commit()
    return MessageResponse(message="Mot de passe modifié. Reconnectez-vous.")


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(body.refresh_token)
    row = get_valid_refresh_token(db, token_hash)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré.",
        )
    revoke_refresh_token(db, token_hash)
    user = row.user
    return _build_token_response(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    revoke_refresh_token(db, hash_refresh_token(body.refresh_token))


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        username=user.ldap_uid,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
    )
