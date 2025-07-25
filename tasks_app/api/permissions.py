from rest_framework.permissions import BasePermission
from tasks_app.models import Task
from kanban_app.models import Column


class IsTaskBoardMember(BasePermission):
    """
    Permission class for task board membership validation.
    
    Allows access to users who are board owners or members.
    For POST requests, validates column access permissions.
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
        Check if user is board owner or member.
        
        Args:
            user: The user object to check
            task: The task object to check board membership for
            
        Returns:
            bool: True if user is board member or owner, False otherwise
        """
        return (user == task.column.board.owner or 
                user in task.column.board.members.all())


class IsTaskAssigneeOrBoardOwner(BasePermission):
    """
    Permission class for task modification validation.
    
    Allows task updates only by assignee or board owner.
    Used for ensuring only relevant users can modify tasks.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user is task assignee or board owner.
        
        Args:
            request: The HTTP request object
            view: The view being accessed
            obj: The task object being accessed
            
        Returns:
            bool: True if user is assignee or board owner, False otherwise
        """
        return (obj.assignee == request.user or 
                request.user == obj.column.board.owner)


class IsCommentAuthorOrBoardOwner(BasePermission):
    """
    Permission class for comment management validation.
    
    Allows comment operations by comment author or board owner.
    Ensures proper access control for comment modifications.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user is comment author or board owner.
        
        Args:
            request: The HTTP request object
            view: The view being accessed
            obj: The comment object being accessed
            
        Returns:
            bool: True if user is comment author or board owner, False otherwise
        """
        return (obj.author == request.user or 
                request.user == obj.task.column.board.owner)


class IsTaskReviewer(BasePermission):
    """
    Permission class for task reviewer validation.
    
    Allows access to users who are assigned as task reviewers.
    Used for review-specific operations and workflow management.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user is assigned as task reviewer.
        
        Args:
            request: The HTTP request object
            view: The view being accessed
            obj: The task object being accessed
            
        Returns:
            bool: True if user is task reviewer, False otherwise
        """
        return request.user in obj.reviewers.all()