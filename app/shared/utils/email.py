import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 10


def enviar_email(destinatario: str, asunto: str, cuerpo: str) -> bool:
    """Envía un email de texto plano por SMTP. Devuelve True si se envió.

    Nunca lanza: un fallo de SMTP no debe romper el endpoint que lo llama (en
    forgot-password cambiaría la respuesta según exista o no el email).
    Config por env vars (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM, SMTP_STARTTLS); sin SMTP_HOST no se envía nada.
    """
    host = os.getenv("SMTP_HOST")
    if not host:
        logger.warning("SMTP_HOST no configurado: no se envió email a %s", destinatario)
        return False

    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    remitente = os.getenv("SMTP_FROM") or user or "no-reply@miifts.com"
    starttls = os.getenv("SMTP_STARTTLS", "true").lower() == "true"

    mensaje = EmailMessage()
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    try:
        # Puerto 465 = TLS implícito; el resto (587/2525) usa STARTTLS.
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=SMTP_TIMEOUT_SECONDS)
        else:
            server = smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT_SECONDS)
        with server:
            if port != 465 and starttls:
                server.starttls()
            if user and password:
                server.login(user, password)
            server.send_message(mensaje)
    except Exception:
        logger.exception("Falló el envío de email a %s", destinatario)
        return False
    return True
