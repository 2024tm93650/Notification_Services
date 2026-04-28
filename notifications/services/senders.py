"""Channel senders — encapsulate the actual transport (SMTP, SMS gateway).

Both senders raise on failure so the dispatcher can mark the notification as
FAILED and update the Prometheus failure counter.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger('notifications')


class EmailSender:
    @staticmethod
    def send(recipient: str, subject: str, message: str) -> None:
        send_mail(
            subject=subject or '(no subject)',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        logger.info(f'Email dispatched to {recipient}')


class SmsSender:
    """Stub SMS sender — logs the message. Replace with Twilio / MSG91 / etc."""

    @staticmethod
    def send(recipient: str, subject: str, message: str) -> None:
        logger.info(f'[SMS STUB] to={recipient} subject={subject!r} body={message!r}')
