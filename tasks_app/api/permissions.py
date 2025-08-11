"""
Permission classes for task operations.
"""
from rest_framework.permissions import BasePermission
from tasks_app.models import Task
from kanban_app.models import Column


class IsTaskBoardMember(BasePermission):
    """
    Permission class for task board membership validation.
    """

    def has_permission(self, request, view):
        """
        Check permission for list/create operations.
        
        Args:
            request: The HTTP request object
            view: The view being accessed
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        if request.method == 'POST':
            return self._validate_column_access(request)
        return True

    def has_object_permission(self, request, view, obj):
        """
        Check permission for specific task objects.
        
        Args:
            request: The HTTP request object
            view: The view being accessed
            obj: The task object being accessed
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        return self._is_board_member(request.user, obj)

    def _validate_column_access(self, request):
        """
        Validate user can access specified column.
        
        Args:
            request: The HTTP request object containing column data
            
        Returns:
            bool: True if user can access column, False otherwise
        """
        column_id = request.data.get('column')
        if not column_id:
            return False
        
        try:
            column = Column.objects.get(id=column_id)
            return self._is_column_accessible(request.user, column)
        except Column.DoesNotExist:
            return False

    def _is_column_accessible(self, user, column):
        """
        Check if user can access the specified column.
        
        Args:
            user: The user object to check
            column: The column object to check access for
            
        Returns:
            bool: True if user can access column, False otherwise
        """
        return (user == column.board.owner or 
                user in column.board.members.all())

    def _is_board_member(self, user, task):
        """
        Check if user is member of task's board.
        
        Args:
            user: User to check
            task: Task instance
            
        Returns:
            bool: True if user is board member
        """
        board = task.column.board
        return (user == board.owner or 
                user in board.members.all())