from django.conf import settings
from django.core.mail import EmailMultiAlternatives


class EmailClient:
    """
    Wrapper sobre el sistema de email de Django. El backend real (consola
    en dev, SMTP en prod) se resuelve por `EMAIL_BACKEND` en settings — este
    cliente no sabe ni le importa cuál está activo.

    Usado por `email_sender.py` (Authentication, verificación/recuperación)
    y por `email_channel.py` (Notifications, HE-13).
    """

    def send(
        self,
        to: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> None:
        message = EmailMultiAlternatives(
            subject=subject,
            body=body_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to],
        )
        if body_html:
            message.attach_alternative(body_html, "text/html")
        message.send(fail_silently=False)
