from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = 'USER', '普通用户'
        ADMIN = 'ADMIN', '管理员'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN


class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capacity = models.PositiveIntegerField()
    location = models.CharField(max_length=120, blank=True)
    equipment = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} (容量: {self.capacity})'


class Booking(models.Model):
    class Status(models.TextChoices):
        BOOKED = 'BOOKED', '已预约'
        CANCELLED = 'CANCELLED', '已取消'

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    title = models.CharField(max_length=150)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    attendees = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.BOOKED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('开始时间必须早于结束时间。')

        if timezone.is_naive(self.start_time) or timezone.is_naive(self.end_time):
            raise ValidationError('预约时间必须包含时区信息。')

        if self.attendees > self.room.capacity:
            raise ValidationError('参会人数超出会议室容量。')

        overlaps = Booking.objects.filter(
            room=self.room,
            status=Booking.Status.BOOKED,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(pk=self.pk)
        if overlaps.exists():
            raise ValidationError('该会议室在当前时间段已被预约。')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.room.name} - {self.title}'


class Notification(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'EMAIL', '邮件'
        MESSAGE = 'MESSAGE', '站内消息'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='notifications')
    channel = models.CharField(max_length=10, choices=Channel.choices)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.user.username} - {self.subject}'
