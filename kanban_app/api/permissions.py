from rest_framework import permissions
from ..models import Board, BoardMembership


class BoardPermission(permissions.BasePermission):
    """
    Custom permission to only allow board members to access boards.
    Owners have full access, admins can edit, others can view.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user has permission for this specific board."""
        if not request.user.is_authenticated:
            return False

        if isinstance(obj, Board):
            board = obj
        else:
            board = getattr(obj, 'board', None)
            if not board:
                return False

        if board.owner == request.user:
            return True

        try:
            membership = BoardMembership.objects.get(user=request.user, board=board)
            
            if request.method in permissions.SAFE_METHODS:
                return True
            
            if request.method in ['POST', 'PUT', 'PATCH']:
                return membership.role in ['ADMIN', 'EDITOR']
            
            if request.method == 'DELETE':
                return membership.role == 'ADMIN' or board.owner == request.user
                
        except BoardMembership.DoesNotExist:
            return False

        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners to edit objects.
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


class IsBoardMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the board.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if hasattr(obj, 'board'):
            board = obj.board
        elif isinstance(obj, Board):
            board = obj
        else:
            return False

        return BoardMembership.objects.filter(
            user=request.user, 
            board=board
        ).exists()


class IsOwnerOrMember(permissions.BasePermission):
    """
    Permission class for board owners and members.
    
    Allows access to users who are board owners or members.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user is board owner or member."""
        if hasattr(obj, 'owner'):
            if obj.owner == request.user:
                return True
            return BoardMembership.objects.filter(user=request.user, board=obj).exists()
        elif hasattr(obj, 'board'):
            board = obj.board
            if board.owner == request.user:
                return True
            return BoardMembership.objects.filter(user=request.user, board=board).exists()
        elif hasattr(obj, 'column'):
            board = obj.column.board
            if board.owner == request.user:
                return True
            return BoardMembership.objects.filter(user=request.user, board=board).exists()
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
        elif hasattr(obj, 'task'):
            return obj.task.column.board.owner == request.user
        return False