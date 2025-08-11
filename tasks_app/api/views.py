"""
API views for tasks.

Provides endpoints for managing tasks in the KanMind application.
"""
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from tasks_app.models import Task, Comment
from tasks_app.api.serializers import TaskSerializer, CommentSerializer  
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
    
    def perform_create(self, serializer):
        """
        Set the creator when creating a task.
        
        Args:
            serializer (TaskSerializer): Serializer with validated data
        """
        serializer.save(created_by=self.request.user)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Update task fields with PATCH request.
        
        Args:
            request (Request): HTTP request with updated fields
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Updated task data
            
        Raises:
            ValidationError: If task data is invalid
        """
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def perform_update(self, serializer):
        """
        Save the updated task instance.
        
        Args:
            serializer (TaskSerializer): Serializer with validated data
        """
        serializer.save()


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
        return Task.objects.filter(assigned_to=self.request.user)


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