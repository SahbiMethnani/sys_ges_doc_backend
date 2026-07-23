# =============================================================
# api/auth/ldap_service.py — Authentification et inscription LDAP
# =============================================================

from ldap3 import SUBTREE, Connection, Server, ALL
from ldap3.core.exceptions import LDAPException

from config import (
    LDAP_BASE_DN,
    LDAP_BIND_DN,
    LDAP_BIND_PASSWORD,
    LDAP_PORT,
    LDAP_SERVER,
    LDAP_USE_SSL,
    LDAP_USER_SEARCH_BASE,
    LDAP_USER_SEARCH_FILTER,
)


class LDAPError(Exception):
    pass


def _server() -> Server:
    host = LDAP_SERVER.replace("ldap://", "").replace("ldaps://", "")
    return Server(host, port=LDAP_PORT, use_ssl=LDAP_USE_SSL, get_info=ALL)


def _admin_connection() -> Connection:
    conn = Connection(
        _server(),
        user=LDAP_BIND_DN,
        password=LDAP_BIND_PASSWORD,
        auto_bind=True,
    )
    if not conn.bound:
        raise LDAPError("Impossible de se connecter au serveur LDAP (compte admin).")
    return conn


def _user_dn(username: str) -> str:
    return f"uid={username},{LDAP_USER_SEARCH_BASE}"


def authenticate_ldap(username: str, password: str) -> dict | None:
    """Vérifie identifiant/mot de passe via bind LDAP. Retourne les attributs ou None."""
    user_dn = _user_dn(username)
    try:
        conn = Connection(_server(), user=user_dn, password=password, auto_bind=True)
        if not conn.bind():
            return None
    except LDAPException:
        return None

    try:
        admin = _admin_connection()
        search_filter = LDAP_USER_SEARCH_FILTER.format(username=username)
        admin.search(
            search_base=LDAP_USER_SEARCH_BASE,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=["mail", "cn", "uid"],
        )
        if not admin.entries:
            return {
                "ldap_uid": username,
                "email": None,
                "display_name": username,
                "ldap_dn": user_dn,
            }
        entry = admin.entries[0]
        mail = entry.mail.value if hasattr(entry, "mail") and entry.mail else None
        cn = entry.cn.value if hasattr(entry, "cn") and entry.cn else username
        return {
            "ldap_uid": username,
            "email": mail,
            "display_name": cn,
            "ldap_dn": user_dn,
        }
    except LDAPException as e:
        raise LDAPError(f"Erreur LDAP : {e}") from e


def register_ldap_user(
    username: str,
    password: str,
    *,
    display_name: str | None = None,
    email: str | None = None,
) -> dict:
    """Crée un utilisateur dans l'annuaire LDAP (rôle applicatif = user dans MySQL)."""
    username = username.strip()
    if not username:
        raise LDAPError("Le nom d'utilisateur est obligatoire.")

    dn = _user_dn(username)
    cn = display_name or username
    mail = email or f"{username}@sysgesdoc.local"

    try:
        conn = _admin_connection()
        conn.search(dn, "(objectClass=*)", search_scope=SUBTREE)
        if conn.entries:
            raise LDAPError("Ce nom d'utilisateur existe déjà dans LDAP.")

        conn.add(
            dn,
            ["inetOrgPerson", "organizationalPerson", "person", "top"],
            {
                "uid": username,
                "cn": cn,
                "sn": cn,
                "mail": mail,
                "userPassword": password,
            },
        )
        if not conn.result["description"] == "success":
            raise LDAPError(conn.result.get("message", "Échec création LDAP."))

        return {
            "ldap_uid": username,
            "email": mail,
            "display_name": cn,
            "ldap_dn": dn,
        }
    except LDAPException as e:
        raise LDAPError(f"Erreur LDAP : {e}") from e


def ensure_users_ou() -> None:
    """Crée l'OU users si elle n'existe pas (utile hors bootstrap Docker)."""
    ou_dn = LDAP_USER_SEARCH_BASE
    try:
        conn = _admin_connection()
        if conn.search(ou_dn, "(objectClass=*)", search_scope=SUBTREE):
            return
        conn.add(
            ou_dn,
            ["organizationalUnit"],
            {"ou": "users"},
        )
    except LDAPException:
        pass
