import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from config import (
    PASSWORD_RESET_EXPIRE_MINUTES,
    PASSWORD_RESET_URL,
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USERNAME,
)


def smtp_is_configured() -> bool:
    return bool(SMTP_HOST and (SMTP_FROM or SMTP_USERNAME))


def send_password_reset_email(recipient: str, token: str) -> None:
    if not smtp_is_configured():
        raise RuntimeError("SMTP n'est pas configuré.")

    separator = "&" if "?" in PASSWORD_RESET_URL else "?"
    reset_url = f"{PASSWORD_RESET_URL}{separator}{urlencode({'token': token})}"
    message = EmailMessage()
    message["Subject"] = "Réinitialisation de votre mot de passe DocRAG"
    message["From"] = SMTP_FROM or SMTP_USERNAME
    message["To"] = recipient
    message.set_content(
        "Une demande de réinitialisation du mot de passe de votre compte DocRAG "
        f"a été effectuée. Utilisez ce lien à usage unique dans les {PASSWORD_RESET_EXPIRE_MINUTES} minutes :\n\n"
        f"{reset_url}\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message."
    )

    context = ssl.create_default_context()
    if SMTP_USE_TLS and SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=15) as server:
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
        return

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        if SMTP_USE_TLS:
            server.starttls(context=context)
        if SMTP_USERNAME:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)