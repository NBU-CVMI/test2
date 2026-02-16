from datetime import datetime, time, timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking, Notification, Room
from .permissions import IsAdminRole, IsOwnerOrAdmin
from .serializers import (
    BookingSerializer,
    LoginSerializer,
    NotificationSerializer,
    RoomSerializer,
)


class AuthView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    queryset = Room.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        room = self.get_object()
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'detail': '请提供 date 参数，格式 YYYY-MM-DD'}, status=400)

        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        tz = timezone.get_current_timezone()
        day_start = timezone.make_aware(datetime.combine(target_date, time(hour=settings.BUSINESS_START_HOUR)), tz)
        day_end = timezone.make_aware(datetime.combine(target_date, time(hour=settings.BUSINESS_END_HOUR)), tz)

        bookings = Booking.objects.filter(
            room=room,
            status=Booking.Status.BOOKED,
            start_time__lt=day_end,
            end_time__gt=day_start,
        ).order_by('start_time')

        busy_slots = []
        for booking in bookings:
            busy_slots.append({'start_time': booking.start_time, 'end_time': booking.end_time, 'title': booking.title})

        available_slots = []
        slot_delta = timedelta(minutes=settings.SLOT_MINUTES)
        cursor = day_start

        while cursor < day_end:
            slot_end = cursor + slot_delta
            conflict = bookings.filter(start_time__lt=slot_end, end_time__gt=cursor).exists()
            if not conflict and cursor >= timezone.now():
                available_slots.append({'start_time': cursor, 'end_time': slot_end})
            cursor = slot_end

        return Response({'room': RoomSerializer(room).data, 'busy_slots': busy_slots, 'available_slots': available_slots})


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer

    def get_queryset(self):
        qs = Booking.objects.select_related('room', 'user')
        if self.request.user.is_admin:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['destroy', 'cancel']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.user_id != request.user.id and not request.user.is_admin:
            return Response({'detail': '无权限取消该预约。'}, status=status.HTTP_403_FORBIDDEN)
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=['status', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(self.get_serializer(notification).data)
