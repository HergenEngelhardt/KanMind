from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from tasks_app.models import Task, Comment
from .serializers import CommentSerializer


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