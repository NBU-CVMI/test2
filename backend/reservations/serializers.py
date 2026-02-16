from django.contrib.auth import authenticate
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import Booking, Notification, Room, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'name', 'capacity', 'location', 'equipment', 'description', 'is_active']


class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    room_detail = RoomSerializer(source='room', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'room',
            'room_detail',
            'user',
            'title',
            'start_time',
            'end_time',
            'attendees',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']

    def validate(self, attrs):
        start_time = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end_time = attrs.get('end_time', getattr(self.instance, 'end_time', None))

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError('开始时间必须早于结束时间。')

        if start_time and start_time < timezone.now():
            raise serializers.ValidationError('不允许预约过去时间。')

        slot_seconds = settings.SLOT_MINUTES * 60
        if start_time and int(start_time.timestamp()) % slot_seconds != 0:
            raise serializers.ValidationError(f'开始时间需按{settings.SLOT_MINUTES}分钟粒度预约。')

        if end_time and int(end_time.timestamp()) % slot_seconds != 0:
            raise serializers.ValidationError(f'结束时间需按{settings.SLOT_MINUTES}分钟粒度预约。')

        room = attrs.get('room', getattr(self.instance, 'room', None))
        attendees = attrs.get('attendees', getattr(self.instance, 'attendees', None))
        if room and attendees and attendees > room.capacity:
            raise serializers.ValidationError('参会人数超过会议室容量。')

        return attrs


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'channel', 'subject', 'content', 'is_read', 'sent_at', 'booking']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('用户名或密码错误。')
        token, _ = Token.objects.get_or_create(user=user)
        return {
            'token': token.key,
            'user': UserSerializer(user).data,
        }
