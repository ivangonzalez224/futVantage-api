"""Email sending.

`send_password_reset_email` is the one function the rest of the app
calls — it doesn't know or care how the email actually gets delivered.
Today it just logs the reset link, which is enough to test the whole
forgot-password flow locally without any external service. Swapping in
a real provider (Postmark, SES, SendGrid, ...) later means rewriting
the body of this one function; nothing else in the codebase needs to
change.
"""

import logging

from app.core.config import get_settings

logger = logging.getLogger("futvantage.email")


def send_password_reset_email(to_email: str, reset_token: str) -> None:
    """Sends a password reset email (in quotes, since this is a dev stand-in).

    Dev/local stand-in: logs the reset link instead of actually
    delivering an email. Look for it in the `uvicorn` console output
    when testing the forgot-password flow locally.
    """
    settings = get_settings()
    reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"

    logger.info(
        "Password reset requested for %s. Reset link (expires in %s minutes): %s",
        to_email,
        settings.password_reset_token_expire_minutes,
        reset_link,
    )
