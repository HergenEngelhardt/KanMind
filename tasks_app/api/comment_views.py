"""
API views for task comments.

Provides views for listing, creating and deleting comments.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from tasks_app.models import Task, Comment
from tasks_app.api.serializers import CommentSerializer
from django.shortcuts import get_object_or_404


class TaskCommentListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating comments for a task.
    
    Provides endpoints to list all comments for a task and create new comments.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return comments for the specified task.
        
        Returns:
            QuerySet: Filtered Comment queryset for the task
        """
        task_id = self.kwargs['task_id']
        return Comment.objects.filter(task_id=task_id).order_by('-created_at')
    
    def perform_create(self, serializer):
        """
        Create a new comment for the specified task.
        
        Args:
            serializer (CommentSerializer): Serializer with validated data
            
        Raises:
            PermissionDenied: If user doesn't have access to the task
        """
        task_id = self.kwargs['task_id']
        task = get_object_or_404(Task, pk=task_id)
        
        self._check_task_access(task)
        serializer.save(task=task, user=self.request.user)
    
    def _check_task_access(self, task):
        """
        Check if user has access to the task's board.
        
        Args:
            task (Task): Task to check
            
        Raises:
            PermissionDenied: If user doesn't have access
        """
        has_access = task.column.board.members.filter(
            id=self.request.user.id
        ).exists()
        
        if not has_access:
            return Response(
                {"error": "You do not have access to this task"}, 
                status=status.HTTP_403_FORBIDDEN
            )


class TaskCommentDeleteView(generics.DestroyAPIView):
    """
    API view for deleting a task comment.
    
    Provides endpoint to delete a specific comment if user is the author.
    """
    queryset = Comment.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Get comment and check permissions.
        
        Returns:
            Comment: The requested comment object
            
        Raises:
            PermissionDenied: If user doesn't own the comment
        """
        comment = super().get_object()
        self._check_comment_ownership(comment)
        return comment
    
    def _check_comment_ownership(self, comment):
        """
        Check if user owns the comment.
        
        Args:
            comment (Comment): Comment to check
            
        Raises:
            PermissionDenied: If user doesn't own the comment
        """
        if comment.user != self.request.user:
            return Response(
                {"error": "You cannot delete this comment"}, 
                status=status.HTTP_403_FORBIDDEN
            )