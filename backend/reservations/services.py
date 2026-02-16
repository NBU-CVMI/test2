from django.conf import settings
from django.core.mail import send_mail

from .models import Notification


def create_booking_notification(booking, subject, content):
    user = booking.user

    send_mail(
        subject=subject,
        message=content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email] if user.email else [],
        fail_silently=True,
    )

    Notification.objects.create(
        user=user,
        booking=booking,
        channel=Notification.Channel.EMAIL,
        subject=subject,
        content=content,
    )

    Notification.objects.create(
        user=user,
        booking=booking,
        channel=Notification.Channel.MESSAGE,
        subject=subject,
        content=content,
    )
