"""
API views for task comments.

Provides views for listing, creating and deleting comments.
"""
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response
from tasks_app.models import Task, Comment
from tasks_app.api.serializers import CommentSerializer
import logging


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
            
        Raises:
            NotFound: If task doesn't exist
        """
        task_id = self.kwargs.get('task_id')
        self._get_task(task_id)  # Validate task exists
        return Comment.objects.filter(task_id=task_id).order_by('-created_at')
    
    def perform_create(self, serializer):
        """
        Create a new comment for the specified task.
        
        Args:
            serializer (CommentSerializer): Serializer with validated data
            
        Raises:
            NotFound: If task doesn't exist
            PermissionDenied: If user doesn't have access to the task
        """
        task_id = self.kwargs.get('task_id')
        task = self._get_task(task_id)
        
        self._check_task_access(task)
        serializer.save(task=task, created_by=self.request.user)
    
    def _get_task(self, task_id):
        """
        Get task by ID.
        
        Args:
            task_id (int): Task ID to find
            
        Returns:
            Task: Task object
            
        Raises:
            NotFound: If task doesn't exist
        """
        try:
            return Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            raise NotFound(f"Task with id {task_id} not found")
    
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
            raise PermissionDenied("You do not have access to this task")


class TaskCommentDeleteView(generics.DestroyAPIView):
    """
    API view for deleting a task comment.
    
    Provides endpoint to delete a specific comment if user is the author.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Get comment and check permissions.
        
        Returns:
            Comment: The requested comment object
            
        Raises:
            NotFound: If comment doesn't exist
            PermissionDenied: If user doesn't own the comment
        """
        task_id = self.kwargs.get('task_id')
        comment_id = self.kwargs.get('pk')
        
        comment = self._get_comment(task_id, comment_id)
        self._check_comment_ownership(comment)
        
        return comment
    
    def _get_comment(self, task_id, comment_id):
        """
        Get comment by task ID and comment ID.
        
        Args:
            task_id (int): Task ID
            comment_id (int): Comment ID
            
        Returns:
            Comment: Comment object
            
        Raises:
            NotFound: If comment doesn't exist
        """
        try:
            return Comment.objects.get(task_id=task_id, id=comment_id)
        except Comment.DoesNotExist:
            raise NotFound("Comment not found")
    
    def _check_comment_ownership(self, comment):
        """
        Check if user owns the comment.
        
        Args:
            comment (Comment): Comment to check
            
        Raises:
            PermissionDenied: If user doesn't own the comment
        """
        if comment.created_by != self.request.user:
            raise PermissionDenied("You cannot delete this comment")
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete the comment.
        
        Args:
            request (Request): HTTP request
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Empty response with 204 status
        """
        comment = self.get_object()
        comment_id = self.kwargs.get('pk')
        task_id = self.kwargs.get('task_id')
        
        comment.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)