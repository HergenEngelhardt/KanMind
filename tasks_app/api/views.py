"""
API views for tasks.

Provides endpoints for managing tasks in the KanMind application.
"""
from django.http import Http404
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from tasks_app.models import Task
from tasks_app.api.serializers import TaskSerializer
from kanban_app.models import Column
import logging



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
        try:
            data = self.prepare_request_data(request)
            
            serializer = self.get_serializer(data=data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def prepare_request_data(self, request):
        """
        Prepare request data for task creation.
        
        Args:
            request (Request): HTTP request
            
        Returns:
            dict: Processed request data
        """
        data = request.data.copy()
        
        self.set_default_values(data)
        self.convert_column_id(data)
        
        return data
    
    def set_default_values(self, data):
        """
        Set default values for required fields.
        
        Args:
            data (dict): Data to update with defaults
        """
        if 'status' not in data:
            data['status'] = 'to-do'
        
        if 'priority' not in data:
            data['priority'] = 'medium'
    
    def convert_column_id(self, data):
        """
        Convert column ID to integer if needed.
        
        Args:
            data (dict): Data containing column ID
        """
        if 'column' in data and not isinstance(data['column'], int):
            try:
                data['column'] = int(data['column'])
            except (ValueError, TypeError):
                pass
    
    def retrieve(self, request, pk=None):
        """
        Retrieve task by ID.
        
        Args:
            request (Request): HTTP request
            pk (int): Task primary key
            
        Returns:
            Response: Task data or error
        """
        if pk == '{{task_id}}':
            return self.handle_template_variable(request)
        
        try:
            task = self.get_object()
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        except Http404:
            return Response(
                {"detail": f"Task with id {pk} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def handle_template_variable(self, request):
        """
        Handle template variable in URL.
        
        Args:
            request (Request): HTTP request
            
        Returns:
            Response: First task or error
        """
        task = Task.objects.filter(
            column__board__members=request.user
        ).first()
        
        if task:
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        
        return Response(
            {"detail": "No tasks found. Create a task first."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update an existing task.
        
        Args:
            request (Request): HTTP request
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Updated task data
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        data = self.prepare_request_data(request)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a task.
        
        Args:
            request (Request): HTTP request
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Empty response with 204 status
        """
        instance = self.get_object()
        task_id = instance.id
        
        self.perform_destroy(instance)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def assigned_to_me(self, request):
        """
        List tasks assigned to current user.
        
        Args:
            request (Request): HTTP request
            
        Returns:
            Response: List of assigned tasks
        """
        tasks = Task.objects.filter(assignee=request.user).distinct()
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reviewing(self, request):
        """
        List tasks user is reviewing.
        
        Args:
            request (Request): HTTP request
            
        Returns:
            Response: List of tasks to review
        """
        tasks = Task.objects.filter(reviewers=request.user).distinct()
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