from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


logger = logging.getLogger(__name__)


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class EmailService:
    def __init__(self) -> None:
        self.enabled = _parse_bool(os.getenv("SMTP_ENABLED"), default=False)
        self.host = os.getenv("SMTP_HOST", "")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", self.username or "no-reply@example.com")
        self.from_name = os.getenv("SMTP_FROM_NAME", "AI News Review")
        self.use_tls = _parse_bool(os.getenv("SMTP_USE_TLS"), default=True)
        self.use_ssl = _parse_bool(os.getenv("SMTP_USE_SSL"), default=False)

    def send_account_created_email(
        self,
        to_email: str,
        username: str,
        role,
        plain_password: str | None = None,
    ) -> bool:
        if not self.enabled:
            logger.info("SMTP disabled: account email skipped for %s", to_email)
            return False

        if not self.host:
            logger.warning("SMTP host missing: account email skipped for %s", to_email)
            return False

        msg = EmailMessage()
        msg["Subject"] = "Compte cree - AI News Review"
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        role_text = self._normalize_role(role)
        password_line = f"Mot de passe: {plain_password}\n\n" if plain_password else ""
        msg.set_content(
            (
                f"Bonjour {username},\n\n"
                "Votre compte a ete cree avec succes.\n"
                f"Role: {role_text}\n"
                f"{password_line}"
                "Vous pouvez maintenant vous connecter a la plateforme.\n\n"
                "Cordialement,\n"
                "Equipe AI News Review"
            )
        )

        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=15) as server:
                    self._login_if_needed(server)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                    if self.use_tls:
                        server.starttls()
                    self._login_if_needed(server)
                    server.send_message(msg)
            return True
        except Exception as exc:
            logger.exception("Failed to send account email to %s: %s", to_email, exc)
            return False

    def _login_if_needed(self, server: smtplib.SMTP) -> None:
        if self.username and self.password:
            server.login(self.username, self.password)

    @staticmethod
    def _normalize_role(role) -> str:
        if hasattr(role, "value"):
            return str(role.value)
        return str(role)
