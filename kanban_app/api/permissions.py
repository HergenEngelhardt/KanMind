from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'board'):
            return obj.board.owner == request.user
        elif hasattr(obj, 'column'):
            return obj.column.board.owner == request.user
        elif hasattr(obj, 'task'):
            return obj.task.column.board.owner == request.user
        return False


class IsOwnerOrMember(permissions.BasePermission):
    """
    Permission class for board owners and members.
    
    Allows access to users who are board owners or members.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user is board owner or member."""
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or request.user in obj.members.all()
        elif hasattr(obj, 'board'):
            board = obj.board
            return board.owner == request.user or request.user in board.members.all()
        elif hasattr(obj, 'column'):
            board = obj.column.board
            return board.owner == request.user or request.user in board.members.all()
        return False


class IsOwner(permissions.BasePermission):
    """
    Permission class for board owners only.
    
    Only allows access to board owners.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user is board owner."""
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'board'):
            return obj.board.owner == request.user
        elif hasattr(obj, 'column'):
            return obj.column.board.owner == request.user
        return False