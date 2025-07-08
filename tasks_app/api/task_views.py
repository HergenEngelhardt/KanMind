from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from django.db import models
import logging

from tasks_app.models import Task
from kanban_app.models import Column
from .serializers import TaskSerializer

logger = logging.getLogger(__name__)


class TaskListCreate(generics.ListCreateAPIView):
    """List tasks for a column or create a new task."""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return tasks based on column_id if provided, otherwise user's tasks."""
        column_id = self.request.query_params.get('column_id')
        if column_id:
            try:
                column = get_object_or_404(Column, id=column_id)
                return Task.objects.filter(column=column)
            except Column.DoesNotExist:
                return Task.objects.none()
        return Task.objects.filter(assignee=self.request.user)

    def perform_create(self, serializer):
        """Set default values when creating a task."""
        try:
            column_id = self.request.data.get('column_id')
            if column_id:
                column = get_object_or_404(Column, id=column_id)
                serializer.save(column=column, created_by=self.request.user)
            else:
                serializer.save(created_by=self.request.user)
                
            logger.info(f"Task created by {self.request.user}: {serializer.instance.title}")
        except Exception as e:
            logger.error(f"Task creation error: {str(e)}")
            raise


class TaskRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a task."""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return tasks that user can access."""
        user = self.request.user
        return Task.objects.filter(
            models.Q(assignee=user) | 
            models.Q(created_by=user) | 
            models.Q(reviewers=user)
        ).distinct()


class TasksAssignedToMeView(generics.ListAPIView):
    """List tasks assigned to the current user."""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return tasks assigned to the current user."""
        try:
            user = self.request.user
            tasks = Task.objects.filter(assignee=user).order_by('-created_at')  
            logger.info(f"Found {tasks.count()} tasks assigned to {user}")
            return tasks
        except Exception as e:
            logger.error(f"Error getting assigned tasks: {str(e)}")
            return Task.objects.none()

    def list(self, request, *args, **kwargs):
        """Override list to add error handling."""
        try:
            response = super().list(request, *args, **kwargs)
            logger.info(f"Successfully returned {len(response.data)} assigned tasks")
            return response
        except Exception as e:
            logger.error(f"Error in TasksAssignedToMeView: {str(e)}")
            return Response(
                {"error": "Failed to fetch assigned tasks", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TasksReviewingView(generics.ListAPIView):
    """List tasks where the current user is a reviewer."""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return tasks where the current user is a reviewer."""
        try:
            user = self.request.user
            tasks = Task.objects.filter(reviewers=user).order_by('-created_at')
            logger.info(f"Found {tasks.count()} tasks for review by {user}")
            return tasks
        except Exception as e:
            logger.error(f"Error getting reviewing tasks: {str(e)}")
            return Task.objects.none()

    def list(self, request, *args, **kwargs):
        """Override list to add error handling."""
        try:
            response = super().list(request, *args, **kwargs)
            logger.info(f"Successfully returned {len(response.data)} reviewing tasks")
            return response
        except Exception as e:
            logger.error(f"Error in TasksReviewingView: {str(e)}")
            return Response(
                {"error": "Failed to fetch reviewing tasks", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )