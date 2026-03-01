from rest_framework import permissions

class IsModerator(permissions.BasePermission):
    """Проверка, является ли пользователь модератором (состоит в группе Moderators)"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='Moderators').exists()


class IsOwner(permissions.BasePermission):
    """Проверка, является ли пользователь владельцем объекта (для объектов с полем owner)"""

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and obj.owner == request.user


class IsModeratorOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if request.user.groups.filter(name='Moderators').exists():
            return True
        return obj.owner == request.user