from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Booking
from .services import create_booking_notification


@receiver(post_save, sender=Booking)
def booking_notification_handler(sender, instance, created, **kwargs):
    if created and instance.status == Booking.Status.BOOKED:
        create_booking_notification(
            instance,
            subject='会议室预约成功通知',
            content=f'您已成功预约 {instance.room.name}，时间 {instance.start_time} - {instance.end_time}。',
        )
    elif instance.status == Booking.Status.CANCELLED:
        create_booking_notification(
            instance,
            subject='会议室预约取消通知',
            content=f'您的预约 {instance.title} 已取消。',
        )
