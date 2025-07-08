from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
import logging

from tasks_app.models import Task, Comment
from .serializers import CommentSerializer

logger = logging.getLogger(__name__)


class CommentListCreateView(generics.ListCreateAPIView):
    """List comments for a task or create a new comment."""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return comments for the specific task."""
        task_id = self.kwargs.get('task_id')
        return Comment.objects.filter(task_id=task_id).order_by('created_at')

    def perform_create(self, serializer):
        """Create comment with task and author."""
        task_id = self.kwargs.get('task_id')
        task = get_object_or_404(Task, id=task_id)
        serializer.save(task=task, author=self.request.user)
        logger.info(f"Comment created by {self.request.user} on task {task.title}")


class CommentDeleteView(generics.DestroyAPIView):
    """Delete a comment."""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return comments that user can delete (only their own)."""
        task_id = self.kwargs.get('task_id')
        return Comment.objects.filter(
            task_id=task_id,
            author=self.request.user
        )

    def destroy(self, request, *args, **kwargs):
        """Delete comment with logging."""
        try:
            instance = self.get_object()
            logger.info(f"Deleting comment {instance.id} by {request.user}")
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error deleting comment: {str(e)}")
            return Response(
                {"error": "Failed to delete comment"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )