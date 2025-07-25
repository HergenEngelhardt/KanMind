from rest_framework import permissions
from ..models import Board, BoardMembership


class BoardPermission(permissions.BasePermission):
    """
    Custom permission to only allow board members to access boards.
    
    Owners have full access, admins can edit, others can view.
    """

    def has_permission(self, request, view):
        """
        Check if user is authenticated.
        
        Args:
            request: HTTP request object
            view: Django view object
            
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission for this specific board.
        
        Args:
            request: HTTP request object
            view: Django view object
            obj: Object being accessed
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        if not request.user.is_authenticated:
            return False

        board = self._get_board_from_object(obj)
        if not board:
            return False

        if board.owner == request.user:
            return True

        return self._check_membership_permission(request, board)

    def _get_board_from_object(self, obj):
        """
        Extract board from object.
        
        Args:
            obj: Object that may contain board reference
            
        Returns:
            Board: Board object or None if not found
        """
        if isinstance(obj, Board):
            return obj
        return getattr(obj, 'board', None)

    def _check_membership_permission(self, request, board):
        """
        Check board membership permissions.
        
        Args:
            request: HTTP request object
            board: Board object
            
        Returns:
            bool: True if user has required permission, False otherwise
        """
        try:
            membership = BoardMembership.objects.get(
                user=request.user, 
                board=board
            )
            return self._evaluate_role_permission(request, membership, board)
        except BoardMembership.DoesNotExist:
            return False

    def _evaluate_role_permission(self, request, membership, board):
        """
        Evaluate permission based on role and request method.
        
        Args:
            request: HTTP request object
            membership: BoardMembership object
            board: Board object
            
        Returns:
            bool: True if permission granted, False otherwise
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if request.method in ['POST', 'PUT', 'PATCH']:
            return membership.role in ['ADMIN', 'EDITOR']
        
        if request.method == 'DELETE':
            return (membership.role == 'ADMIN' or 
                    board.owner == request.user)
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners to edit objects.
    
    Read access is granted to all, write access only to owners.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user can access object based on ownership.
        
        Args:
            request: HTTP request object
            view: Django view object
            obj: Object being accessed
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        return self._check_ownership(request.user, obj)

    def _check_ownership(self, user, obj):
        """
        Check if user owns the object through various relationships.
        
        Args:
            user: User object
            obj: Object to check ownership for
            
        Returns:
            bool: True if user owns object, False otherwise
        """
        if hasattr(obj, 'owner'):
            return obj.owner == user
        elif hasattr(obj, 'board'):
            return obj.board.owner == user
        elif hasattr(obj, 'column'):
            return obj.column.board.owner == user
        elif hasattr(obj, 'task'):
            return obj.task.column.board.owner == user
        return False


class IsBoardMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the board.
    
    Only authenticated board members can access resources.
    """

    def has_permission(self, request, view):
        """
        Check if user is authenticated.
        
        Args:
            request: HTTP request object
            view: Django view object
            
        Returns:
            bool: True if user is authenticated, False otherwise
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if user is a member of the related board.
        
        Args:
            request: HTTP request object
            view: Django view object
            obj: Object being accessed
            
        Returns:
            bool: True if user is board member, False otherwise
        """
        if not request.user.is_authenticated:
            return False

        board = self._extract_board(obj)
        if not board:
            return False

        return BoardMembership.objects.filter(
            user=request.user, 
            board=board
        ).exists()

    def _extract_board(self, obj):
        """
        Extract board from object.
        
        Args:
            obj: Object that may contain board reference
            
        Returns:
            Board: Board object or None if not found
        """
        if hasattr(obj, 'board'):
            return obj.board
        elif isinstance(obj, Board):
            return obj
        return None


class IsOwnerOrMember(permissions.BasePermission):
    """
    Permission class for board owners and members.
    
    Allows access to users who are board owners or members.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user is board owner or member.
        
        Args:
            request: HTTP request object
            view: Django view object
            obj: Object being accessed
            
        Returns:
            bool: True if user is owner or member, False otherwise
        """
        user = request.user
        
        if hasattr(obj, 'owner'):
            return self._check_owner_or_member_for_board(user, obj)
        elif hasattr(obj, 'board'):
            return self._check_owner_or_member_for_board(user, obj.board)
        elif hasattr(obj, 'column'):
            return self._check_owner_or_member_for_board(user, obj.column.board)
        
        return False

    def _check_owner_or_member_for_board(self, user, board):
        """
        Check if user is owner or member of specific board.
        
        Args:
            user: User object
            board: Board object
            
        Returns:
            bool: True if user is owner or member, False otherwise
        """
        if board.owner == user:
            return True
        return BoardMembership.objects.filter(
            user=user, 
            board=board
        ).exists()


class IsOwner(permissions.BasePermission):
    """
    Permission class for board owners only.
    
    Only allows access to board owners.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user is board owner.
        
        Args:
            request: HTTP request object
            view: Django view object
            obj: Object being accessed
            
        Returns:
            bool: True if user is owner, False otherwise
        """
        user = request.user
        
        if hasattr(obj, 'owner'):
            return obj.owner == user
        elif hasattr(obj, 'board'):
            return obj.board.owner == user
        elif hasattr(obj, 'column'):
            return obj.column.board.owner == user
        elif hasattr(obj, 'task'):
            return obj.task.column.board.owner == user
        
        return False