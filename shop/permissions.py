from rest_framework import permissions


class IsUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='user'):
            return True
        return False


class CategoryPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        return request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            return True
        return request.user.is_superuser