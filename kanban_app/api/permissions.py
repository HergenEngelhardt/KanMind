from rest_framework.permissions import BasePermission


class IsOwnerOrMember(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user or request.user in obj.members.all()


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user