"""
API views for tasks.

Provides endpoints for managing tasks in the KanMind application.
"""
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from tasks_app.models import Task
from tasks_app.api.serializers import TaskSerializer
from kanban_app.models import Column
import logging

logger = logging.getLogger(__name__)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks.
    
    Provides endpoints for creating, retrieving, updating and deleting tasks.
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return tasks accessible to current user.
        
        Returns:
            QuerySet: Filtered Task queryset for the current user
        """
        user = self.request.user
        return Task.objects.filter(
            column__board__members=user
        ).distinct()
    
    def create(self, request):
        """
        Create a new task.
        
        Args:
            request (Request): HTTP request with task data
            
        Returns:
            Response: Created task data
            
        Raises:
            ValidationError: If task data is invalid
        """
        self._validate_required_fields(request.data)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        task = self._save_task(serializer, request.user)
        logger.info(f"Task created: {task.title}")
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _validate_required_fields(self, data):
        """
        Validate required fields for task creation.
        
        Args:
            data (dict): Task data to validate
            
        Raises:
            ValidationError: If required fields are missing
        """
        if not data.get('column'):
            raise ValidationError({"column": "Column field is required"})
        
        if not data.get('title'):
            raise ValidationError({"title": "Title field is required"})
    
    def _save_task(self, serializer, user):
        """
        Save task with the current user as creator.
        
        Args:
            serializer (TaskSerializer): Validated serializer
            user (User): User creating the task
            
        Returns:
            Task: Created task
        """
        return serializer.save(created_by=user)
    
    @action(detail=False, methods=['get'])
    def assigned_to_me(self, request):
        """
        List tasks assigned to current user.
        
        Args:
            request: HTTP request
            
        Returns:
            Response: List of assigned tasks
        """
        tasks = Task.objects.filter(
            assignee=request.user
        ).distinct()
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reviewing(self, request):
        """
        List tasks user is reviewing.
        
        Args:
            request: HTTP request
            
        Returns:
            Response: List of tasks to review
        """
        tasks = Task.objects.filter(
            reviewers=request.user
        ).distinct()
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class TaskAssignedListView(generics.ListAPIView):
    """
    API view for listing tasks assigned to the current user.
    
    Provides a read-only endpoint for tasks assigned to the authenticated user.
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return tasks assigned to current user.
        
        Returns:
            QuerySet: Filtered Task queryset assigned to the user
        """
        return Task.objects.filter(assignee=self.request.user)


class TaskReviewingListView(generics.ListAPIView):
    """
    API view for listing tasks where current user is a reviewer.
    
    Provides a read-only endpoint for tasks the authenticated user is reviewing.
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return tasks where current user is a reviewer.
        
        Returns:
            QuerySet: Filtered Task queryset for review tasks
        """
        return Task.objects.filter(reviewers=self.request.user)