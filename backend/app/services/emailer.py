from __future__ import annotations

import smtplib

from email.message import EmailMessage

from app.core.config import settings

from app.core.logging import logger

def send_email(*, to_email: str, subject: str, body: str) -> None:

    """
    Sends an email via SMTP. This is intentionally only used for DB-registered businesses.
    If SMTP is not configured, the email is skipped (logged) in dev.
    """

    if not (settings.smtp_host and settings.smtp_from_email):

        logger.info("email.skipped", reason="smtp_not_configured", to=to_email, subject=subject)

        return

    msg = EmailMessage()

    msg["From"] = settings.smtp_from_email

    msg["To"] = to_email

    msg["Subject"] = subject

    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:

        server.ehlo()

        try:

            server.starttls()

            server.ehlo()

        except smtplib.SMTPException:

            

            pass

        if settings.smtp_username and settings.smtp_password:

            server.login(settings.smtp_username, settings.smtp_password)

        server.send_message(msg)

    logger.info("email.sent", to=to_email, subject=subject)

