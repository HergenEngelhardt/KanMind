"""
Custom permissions for tasks API.

This module contains custom permission classes for task-related views.
"""
from rest_framework import permissions
from kanban_app.models import BoardMembership

class IsBoardMember(permissions.BasePermission):
    """
    Custom permission to check if user is a member of the board.
    
    This permission is used for board-related task operations.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user is a member of the board.
        
        Args:
            request (Request): The HTTP request object.
            view (APIView): The view that triggered the permission check.
            obj (Board): The board object to check permissions against.
            
        Returns:
            bool: True if the user is a member of the board, False otherwise.
        """
        user = request.user
        if not user.is_authenticated:
            return False
            
        if obj.owner == user:
            return True
            
        return BoardMembership.objects.filter(
            board=obj,
            user=user
        ).exists()