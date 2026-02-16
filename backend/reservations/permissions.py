from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = '仅管理员可执行该操作。'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsOwnerOrAdmin(BasePermission):
    message = '仅预约创建者或管理员可操作。'

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id or request.user.is_admin
