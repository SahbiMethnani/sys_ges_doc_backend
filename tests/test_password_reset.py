import pytest

from api.auth.ldap_service import LDAPError, change_ldap_password
from api.auth import email_service
from api.auth.security import (
    generate_password_reset_token,
    hash_password_reset_token,
)
from api.auth.router import forgot_password
from api.models import ForgotPasswordRequest, ResetPasswordRequest


@pytest.mark.unit
def test_reset_token_is_random_and_only_hash_is_stored():
    first = generate_password_reset_token()
    second = generate_password_reset_token()

    assert first != second
    assert len(hash_password_reset_token(first)) == 64
    assert hash_password_reset_token(first) != first


@pytest.mark.unit
def test_new_password_request_enforces_length():
    with pytest.raises(ValueError):
        ResetPasswordRequest(token="valid-token", new_password="short")

    request = ResetPasswordRequest(token="valid-token", new_password="long-enough-password")
    assert request.new_password == "long-enough-password"


@pytest.mark.unit
def test_change_ldap_password_replaces_user_password(monkeypatch):
    class FakeConnection:
        result = {"description": "success", "message": ""}

        def modify(self, dn, changes):
            self.dn = dn
            self.changes = changes
            return True

    fake_connection = FakeConnection()
    monkeypatch.setattr(
        "api.auth.ldap_service._admin_connection", lambda: fake_connection
    )

    change_ldap_password("uid=demo,ou=users,dc=sysgesdoc,dc=local", "new-password")

    assert fake_connection.dn == "uid=demo,ou=users,dc=sysgesdoc,dc=local"
    assert "userPassword" in fake_connection.changes


@pytest.mark.unit
def test_change_ldap_password_raises_when_ldap_refuses(monkeypatch):
    class FakeConnection:
        result = {"description": "insufficientAccessRights", "message": "denied"}

        def modify(self, dn, changes):
            return False

    monkeypatch.setattr(
        "api.auth.ldap_service._admin_connection", FakeConnection
    )

    with pytest.raises(LDAPError, match="denied"):
        change_ldap_password("uid=demo,ou=users,dc=sysgesdoc,dc=local", "new-password")


@pytest.mark.unit
def test_reset_email_contains_single_use_link(monkeypatch):
    class FakeSMTP:
        message = None

        def __init__(self, host, port, timeout):
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def starttls(self, context):
            self.tls_enabled = True

        def login(self, username, password):
            self.username = username

        def send_message(self, message):
            FakeSMTP.message = message

    monkeypatch.setattr(email_service, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(email_service, "SMTP_PORT", 587)
    monkeypatch.setattr(email_service, "SMTP_USERNAME", "sender@example.test")
    monkeypatch.setattr(email_service, "SMTP_PASSWORD", "test-secret")
    monkeypatch.setattr(email_service, "SMTP_FROM", "sender@example.test")
    monkeypatch.setattr(email_service, "SMTP_USE_TLS", True)
    monkeypatch.setattr(email_service, "PASSWORD_RESET_URL", "http://localhost:4200/reset-password")
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)

    email_service.send_password_reset_email("user@example.test", "one-time-token")

    assert FakeSMTP.message["To"] == "user@example.test"
    assert "token=one-time-token" in FakeSMTP.message.get_content()


@pytest.mark.unit
def test_forgot_password_returns_generic_response_for_unknown_user(monkeypatch):
    monkeypatch.setattr("api.auth.router.get_user_by_username", lambda db, username: None)

    response = forgot_password(ForgotPasswordRequest(username="unknown"), db=object())

    assert response.message.startswith("Si le compte existe")