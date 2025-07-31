from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from django.db import models
import logging

from tasks_app.models import Task, Comment
from .serializers import CommentSerializer

logger = logging.getLogger(__name__)


class CommentListCreateView(generics.ListCreateAPIView):
    """
    List comments for a task or create a new comment.
    """
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return comments for the specified task.
        
        Returns:
            QuerySet: Comments for the task if user has access
        """
        task_id = self.kwargs.get('task_id')
        if not self._user_has_task_access(task_id):
            return Comment.objects.none()
        return Comment.objects.filter(task_id=task_id).order_by('-created_at')

    def perform_create(self, serializer):
        """
        Create comment with current user and task.
        
        Args:
            serializer: Comment serializer instance
            
        Raises:
            PermissionDenied: If user cannot comment on task
        """
        task_id = self.kwargs.get('task_id')
        task = get_object_or_404(Task, id=task_id)
        
        if not self._user_can_comment_on_task(task):
            raise PermissionDenied("You don't have permission to comment on this task")
        
        serializer.save(author=self.request.user, task=task)

    def create(self, request, *args, **kwargs):
        """
        Override create to return proper response format.
        
        Args:
            request: HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: HTTP response with comment data or validation errors
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        logger.error(f"Comment creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _user_has_task_access(self, task_id):
        """
        Check if user has access to the task.
        
        Args:
            task_id: ID of the task to check access for
            
        Returns:
            bool: True if user has access, False otherwise
        """
        try:
            task = Task.objects.get(id=task_id)
            board = task.column.board
            return (board.owner == self.request.user or 
                   board.boardmembership_set.filter(user=self.request.user).exists())
        except Task.DoesNotExist:
            return False

    def _user_can_comment_on_task(self, task):
        """
        Check if user can comment on the given task.
        
        Args:
            task: Task instance to check permissions for
            
        Returns:
            bool: True if user can comment, False otherwise
        """
        board = task.column.board
        return (board.owner == self.request.user or 
               board.boardmembership_set.filter(user=self.request.user).exists())


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a comment.
    """
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Get comment by task_id and comment_id.
        
        Returns:
            Comment: Comment instance
            
        Raises:
            Http404: If comment not found
        """
        task_id = self.kwargs.get('task_id')
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, id=comment_id, task_id=task_id)

    def get_queryset(self):
        """
        Return comments that user can access.
        
        Returns:
            QuerySet: Comments the user has access to based on board permissions
        """
        task_id = self.kwargs.get('task_id')
        if not task_id:
            return Comment.objects.none()
        
        user = self.request.user
        return Comment.objects.filter(
            task_id=task_id
        ).filter(
            models.Q(task__column__board__owner=user) | 
            models.Q(task__column__board__boardmembership__user=user)
        )

    def destroy(self, request, *args, **kwargs):
        """
        Delete comment with proper permissions.
        
        Args:
            request: HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: HTTP response indicating success or failure
            
        Raises:
            PermissionDenied: If user cannot delete comment
        """
        try:
            instance = self.get_object()
            
            if not self._user_can_delete_comment(instance, request.user):
                return Response(
                    {"error": "You can only delete your own comments or as board owner"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return self._perform_comment_deletion(instance, request.user)
            
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting comment: {str(e)}")
            return Response({"error": "Failed to delete comment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _user_can_delete_comment(self, comment, user):
        """
        Check if user can delete the comment.
        
        Args:
            comment: Comment instance to check permissions for
            user: User attempting to delete the comment
            
        Returns:
            bool: True if user can delete, False otherwise
        """
        if comment.author == user:
            return True
        
        board_owner = comment.task.column.board.owner
        return board_owner == user

    def _perform_comment_deletion(self, instance, user):
        """
        Perform the actual comment deletion and logging.
        
        Args:
            instance: Comment instance to delete
            user: User performing the deletion
            
        Returns:
            Response: HTTP response indicating successful deletion
        """
        comment_id = instance.id
        task_title = instance.task.title
        self.perform_destroy(instance)
        
        logger.info(f"Comment {comment_id} deleted by {user} from task '{task_title}'")
        return Response(status=status.HTTP_204_NO_CONTENT)