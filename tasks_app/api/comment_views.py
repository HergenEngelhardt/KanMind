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
    """List comments for a task or create a new comment."""
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return comments for the specific task ordered by creation time."""
        task_id = self.kwargs.get('task_id')
        if not task_id:
            return Comment.objects.none()
        
        try:
            task = Task.objects.get(id=task_id)
            board = task.column.board
            if not (board.owner == self.request.user or self.request.user in board.members.all()):
                return Comment.objects.none()
        except Task.DoesNotExist:
            return Comment.objects.none()
        
        return Comment.objects.filter(task_id=task_id).order_by('created_at')

    def perform_create(self, serializer):
        """Create comment with task and author."""
        task_id = self.kwargs.get('task_id')
        task = get_object_or_404(Task, id=task_id)
        
        board = task.column.board
        if not (board.owner == self.request.user or self.request.user in board.members.all()):
            raise PermissionDenied("You don't have permission to comment on this task")
        
        comment = serializer.save(task=task, author=self.request.user)
        logger.info(f"Comment {comment.id} created by {self.request.user} on task '{task.title}'")

    def create(self, request, *args, **kwargs):
        """Override create to return proper response format."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        
        logger.error(f"Comment creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a comment."""
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return comments that user can access."""
        task_id = self.kwargs.get('task_id')
        if not task_id:
            return Comment.objects.none()
        
        user = self.request.user
        return Comment.objects.filter(
            task_id=task_id
        ).filter(
            models.Q(task__column__board__owner=user) | 
            models.Q(task__column__board__members=user)
        )

    def destroy(self, request, *args, **kwargs):
        """Delete comment with proper permissions."""
        try:
            instance = self.get_object()
            
            # Only author or board owner can delete
            if instance.author != request.user:
                board_owner = instance.task.column.board.owner
                if board_owner != request.user:
                    return Response(
                        {"error": "You can only delete your own comments or as board owner"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            comment_id = instance.id
            task_title = instance.task.title
            self.perform_destroy(instance)
            
            logger.info(f"Comment {comment_id} deleted by {request.user} from task '{task_title}'")
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Comment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting comment: {str(e)}")
            return Response({"error": "Failed to delete comment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)