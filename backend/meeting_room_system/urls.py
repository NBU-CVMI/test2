from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from reservations.views import (
    AuthView,
    BookingViewSet,
    NotificationViewSet,
    RoomViewSet,
)

router = DefaultRouter()
router.register('rooms', RoomViewSet, basename='room')
router.register('bookings', BookingViewSet, basename='booking')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', AuthView.as_view(), name='login'),
    path('api/', include(router.urls)),
]
