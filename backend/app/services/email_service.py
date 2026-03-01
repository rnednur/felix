"""
Email service for sending transactional emails.

Uses SMTP with optional TLS. If SMTP is not configured, falls back to
printing the reset link to the server console (useful for development).
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD)


def _send_email(to_address: str, subject: str, html_body: str, text_body: str) -> None:
    """Send an email via SMTP. Raises on failure."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
    msg["To"] = to_address

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM_ADDRESS, to_address, msg.as_string())


def send_password_reset_email(to_address: str, reset_token: str) -> None:
    """
    Send a password reset email.

    If SMTP is not configured, logs the reset link to the console instead
    so development can still work without email setup.
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    subject = f"Reset your {settings.EMAIL_FROM_NAME} password"

    text_body = f"""Hi,

You requested a password reset for your {settings.EMAIL_FROM_NAME} account.

Click the link below to set a new password. This link expires in 1 hour.

{reset_url}

If you didn't request this, you can safely ignore this email.

— The {settings.EMAIL_FROM_NAME} Team
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin:0;padding:0;background-color:#f4f6f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f9;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="100%" style="max-width:520px;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#3b82f6,#6366f1);padding:32px 40px;text-align:center;">
              <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-0.3px;">
                {settings.EMAIL_FROM_NAME}
              </h1>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <h2 style="margin:0 0 12px;color:#111827;font-size:20px;font-weight:600;">
                Reset your password
              </h2>
              <p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
                We received a request to reset the password for your account.
                Click the button below to choose a new password.
                This link expires in <strong>1 hour</strong>.
              </p>

              <!-- CTA Button -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" style="padding:4px 0 28px;">
                    <a href="{reset_url}"
                       style="display:inline-block;padding:14px 32px;background:#3b82f6;color:#ffffff;
                              font-size:15px;font-weight:600;text-decoration:none;border-radius:8px;
                              letter-spacing:0.2px;">
                      Reset Password
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 8px;color:#9ca3af;font-size:13px;">
                Or copy and paste this link into your browser:
              </p>
              <p style="margin:0 0 28px;word-break:break-all;">
                <a href="{reset_url}" style="color:#3b82f6;font-size:13px;">{reset_url}</a>
              </p>

              <hr style="border:none;border-top:1px solid #e5e7eb;margin:0 0 24px;">

              <p style="margin:0;color:#9ca3af;font-size:13px;line-height:1.5;">
                If you didn't request a password reset, you can safely ignore this email.
                Your password will not change.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #e5e7eb;">
              <p style="margin:0;color:#9ca3af;font-size:12px;">
                © {settings.EMAIL_FROM_NAME}. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    if not _smtp_configured():
        # Development fallback: print to console
        logger.warning(
            "SMTP not configured. Password reset link for %s:\n%s",
            to_address,
            reset_url,
        )
        return

    try:
        _send_email(to_address, subject, html_body, text_body)
        logger.info("Password reset email sent to %s", to_address)
    except Exception as exc:
        logger.error("Failed to send password reset email to %s: %s", to_address, exc)
