import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config.settings import settings


def _send(to: str, subject: str, body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = settings.MAIL_FROM
    msg["To"]      = to
    msg.attach(MIMEText(body, "plain", "utf-8"))
    with smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT, timeout=5) as smtp:
        smtp.sendmail(settings.MAIL_FROM, [to], msg.as_string())


def send_admin_developer_pending(developer_name: str, support_email: str) -> None:
    _send(
        to      = settings.MAIL_FROM,
        subject = f"[Burnt] Nuevo developer pendiente de aprobación: {developer_name}",
        body    = (
            f"El developer '{developer_name}' acaba de registrarse y está pendiente de aprobación.\n\n"
            f"Email de soporte: {support_email}\n\n"
            "Accede al panel de administración para aprobar o rechazar la cuenta:\n"
            "http://localhost:8000/views/developer/"
        ),
    )


def send_admin_title_pending(title_name: str, developer_name: str) -> None:
    _send(
        to      = settings.MAIL_FROM,
        subject = f"[Burnt] Nuevo título pendiente de aprobación: {title_name}",
        body    = (
            f"El developer '{developer_name}' ha creado el título '{title_name}', pendiente de aprobación.\n\n"
            "Accede al panel de administración para aprobarlo:\n"
            "http://localhost:8000/views/title/"
        ),
    )


def send_otp_code(to: str, code: str) -> None:
    _send(
        to      = to,
        subject = "[Burnt] Tu código de verificación",
        body    = (
            f"Tu código de verificación es: {code}\n\n"
            "Este código expira en 10 minutos.\n"
            "Si no has solicitado este código, ignora este mensaje."
        ),
    )


def send_admin_review_pending(customer_name: str, title_name: str) -> None:
    _send(
        to      = settings.MAIL_FROM,
        subject = f"[Burnt] Nueva review pendiente: {customer_name} → {title_name}",
        body    = (
            f"El customer '{customer_name}' ha escrito una review para '{title_name}' y está pendiente de moderación.\n\n"
            "Accede al panel de administración para publicarla o rechazarla:\n"
            "http://localhost:8000/views/review/"
        ),
    )


def send_admin_contact(sender: str, message: str) -> None:
    _send(
        to      = settings.MAIL_FROM,
        subject = f"[Burnt] Nuevo mensaje de contacto: {sender}",
        body    = f"De: {sender}\n\nMensaje:\n{message}",
    )
