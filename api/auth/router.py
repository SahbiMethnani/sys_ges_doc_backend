# =============================================================
# api/auth/router.py — Connexion, inscription, profil
# =============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.auth.dependencies import get_current_user
from api.auth.ldap_service import LDAPError, authenticate_ldap, register_ldap_user
from api.auth.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expires_at,
)
from api.auth.user_service import (
    create_user_from_registration,
    get_valid_refresh_token,
    revoke_refresh_token,
    store_refresh_token,
    sync_user_after_ldap_login,
)
from api.db.models import User
from api.db.session import get_db
from api.models import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from config import JWT_ACCESS_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentification"])


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
    """
    Inscription : création dans LDAP + MySQL avec le rôle « user ».
    Les administrateurs sont définis uniquement en base (ex. Sahbi).
    """
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
