import logging
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from tasks_app.models import Task, Comment
from kanban_app.models import Column, Board
from .serializers import TaskSerializer, CommentSerializer
from .permissions import (
    IsTaskBoardMember, 
    IsTaskAssigneeOrBoardOwner, 
    IsCommentAuthorOrBoardOwner
)

logger = logging.getLogger(__name__)


class TaskListCreate(generics.ListCreateAPIView):
    """
    List tasks or create a new task.
    
    GET: Returns tasks filtered by column or user's boards
    POST: Creates a new task in specified column with permission check
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return tasks filtered by column or user's boards."""
        column_id = self.request.query_params.get("column")
        if column_id:
            if not column_id.isdigit():
                from rest_framework.exceptions import ValidationError
                raise ValidationError("Invalid column ID")
            return Task.objects.filter(column_id=column_id)
        return self._get_user_board_tasks()

    def _get_user_board_tasks(self):
        """Get tasks from boards where user is owner or member."""
        user_boards = Board.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).distinct()
        return Task.objects.filter(column__board__in=user_boards)

    def perform_create(self, serializer):
        """Ensure the user has permission to create tasks in the specified column."""
        column = serializer.validated_data['column']
        board = column.board
        
        if not (board.owner == self.request.user or self.request.user in board.members.all()):
            raise PermissionDenied("You don't have permission to create tasks in this board.")
        
        serializer.save()

    def _get_user_board_tasks(self):
        """Get all tasks from user's owned boards."""
        return Task.objects.filter(column__board__owner=self.request.user)

    def _get_column_or_raise(self, column_id):
        """Get column or raise PermissionDenied."""
        try:
            return Column.objects.get(id=column_id)
        except Column.DoesNotExist:
            raise PermissionDenied("Column does not exist")

    def _validate_column_permissions(self, column):
        """Validate user has permission to add tasks to column."""
        if column.board.owner != self.request.user:
            raise PermissionDenied(
                "You don't have permission to add tasks to this column"
            )


class TaskRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific task.
    
    Different permission classes based on request method.
    Update requires assignee or board owner permissions.
    """
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskBoardMember]

    def get_permissions(self):
        """Set permissions based on request method."""
        if self.request.method in ['PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsTaskAssigneeOrBoardOwner()]
        return [permissions.IsAuthenticated(), IsTaskBoardMember()]

    def get_queryset(self):
        """Return tasks from user's boards (owned or member)."""
        return Task.objects.filter(
            models.Q(column__board__owner=self.request.user)
            | models.Q(column__board__members=self.request.user)
        ).distinct()
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
        
    def partial_update(self, request, *args, **kwargs):
        """Handle partial task update with error handling."""
        try:
            return super().partial_update(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Task update error: {str(e)}")
            return self._update_error_response()

    def _update_error_response(self):
        """Return error response for update failures."""
        return Response(
            {"error": "An error occurred while updating the task."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class TasksAssignedToMeView(generics.ListAPIView):
    """
    List tasks assigned to the current user.
    
    Returns all tasks where the authenticated user is the assignee.
    """
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return tasks assigned to current user."""
        return Task.objects.filter(assignee=self.request.user)


class TasksReviewingView(generics.ListAPIView):
    """
    List tasks being reviewed by the current user.
    
    Returns all tasks where the authenticated user is a reviewer.
    """
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return tasks being reviewed by current user."""
        return Task.objects.filter(reviewers=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    """
    List comments for a task or create a new comment.
    
    GET: Returns comments for specified task (with permission check)
    POST: Creates new comment on task (requires board membership)
    """
    
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return comments for task with permission check."""
        task_id = self.kwargs.get("task_id")
        task = self._get_task_or_404(task_id)
        self._validate_task_access(task)
        return Comment.objects.filter(task_id=task_id)

    def perform_create(self, serializer):
        """Create comment with permission validation."""
        task_id = self.kwargs.get("task_id")
        task = self._get_task_or_404(task_id)
        self._validate_comment_permissions(task)
        serializer.save(task=task, author=self.request.user)

    def _get_task_or_404(self, task_id):
        """Get task or raise 404."""
        return get_object_or_404(Task, id=task_id)

    def _validate_task_access(self, task):
        """Validate user can view task comments."""
        if not self._is_board_member(task):
            raise PermissionDenied(
                "You don't have permission to view comments for this task"
            )

    def _validate_comment_permissions(self, task):
        """Validate user can comment on task."""
        if not self._is_board_member(task):
            raise PermissionDenied(
                "You don't have permission to comment on this task"
            )

    def _is_board_member(self, task):
        """Check if user is board owner or member."""
        board = task.column.board
        return (board.owner == self.request.user or 
                self.request.user in board.members.all())


class CommentDeleteView(generics.DestroyAPIView):
    """
    Delete a specific comment.
    
    Only comment author or board owner can delete comments.
    """
    
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return comments for specified task."""
        task_id = self.kwargs.get("task_id")
        return Comment.objects.filter(task_id=task_id)

    def destroy(self, request, *args, **kwargs):
        """Delete comment with permission check."""
        comment = self.get_object()
        self._validate_delete_permissions(comment)
        return super().destroy(request, *args, **kwargs)

    def _validate_delete_permissions(self, comment):
        """Validate user can delete comment."""
        if not self._can_delete_comment(comment):
            raise PermissionDenied(
                "You don't have permission to delete this comment"
            )

    def _can_delete_comment(self, comment):
        """Check if user can delete comment."""
        return (comment.author == self.request.user or 
                comment.task.column.board.owner == self.request.user)