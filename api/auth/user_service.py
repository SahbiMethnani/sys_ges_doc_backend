# =============================================================
# api/auth/user_service.py — Synchronisation utilisateurs MySQL
# =============================================================

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from api.db.models import RefreshToken, User
from config import SEED_ADMIN_DISPLAY_NAME, SEED_ADMIN_USERNAME


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.ldap_uid == username).first()


def ensure_admin_seed(db: Session) -> None:
    """Garantit l'enregistrement MySQL de l'admin initial (Sahbi)."""
    user = get_user_by_username(db, SEED_ADMIN_USERNAME)
    if user is None:
        db.add(
            User(
                ldap_uid=SEED_ADMIN_USERNAME,
                display_name=SEED_ADMIN_DISPLAY_NAME,
                ldap_dn=f"uid={SEED_ADMIN_USERNAME},ou=users,dc=sysgesdoc,dc=local",
                role="admin",
                is_active=True,
            )
        )
        db.commit()
    elif user.role != "admin":
        user.role = "admin"
        db.commit()


def sync_user_after_ldap_login(db: Session, ldap_info: dict) -> User:
    user = get_user_by_username(db, ldap_info["ldap_uid"])
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if user is None:
        user = User(
            ldap_uid=ldap_info["ldap_uid"],
            email=ldap_info.get("email"),
            display_name=ldap_info.get("display_name"),
            ldap_dn=ldap_info.get("ldap_dn"),
            role="user",
            is_active=True,
            last_login_at=now,
        )
        db.add(user)
    else:
        if ldap_info.get("email"):
            user.email = ldap_info["email"]
        if ldap_info.get("display_name"):
            user.display_name = ldap_info["display_name"]
        if ldap_info.get("ldap_dn"):
            user.ldap_dn = ldap_info["ldap_dn"]
        user.last_login_at = now

    db.commit()
    db.refresh(user)
    return user


def create_user_from_registration(db: Session, ldap_info: dict) -> User:
    existing = get_user_by_username(db, ldap_info["ldap_uid"])
    if existing:
        raise ValueError("Cet utilisateur existe déjà dans l'application.")

    user = User(
        ldap_uid=ldap_info["ldap_uid"],
        email=ldap_info.get("email"),
        display_name=ldap_info.get("display_name"),
        ldap_dn=ldap_info.get("ldap_dn"),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def store_refresh_token(db: Session, user_id: int, token_hash: str, expires_at) -> None:
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at.replace(tzinfo=None)
            if expires_at.tzinfo
            else expires_at,
        )
    )
    db.commit()


def revoke_refresh_token(db: Session, token_hash: str) -> None:
    row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
        .first()
    )
    if row:
        row.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()


def get_valid_refresh_token(db: Session, token_hash: str) -> RefreshToken | None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .first()
    )
