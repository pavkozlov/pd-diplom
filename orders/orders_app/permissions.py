from rest_framework import permissions


class IsShop(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return 'shop' == request.user.type


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.owner == request.user


class IsOwnerOfProfile(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user
