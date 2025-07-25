from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import logging

from ..models import Task
from .serializers import TaskSerializer, TaskUpdateSerializer
from kanban_app.models import Board, BoardMembership, Column

logger = logging.getLogger(__name__)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Task CRUD operations and custom actions.
    
    Provides standard REST API endpoints for tasks with additional
    functionality for moving tasks between columns.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get queryset for Task objects with optimized database queries.
        
        Returns:
            QuerySet: All Task objects with related data prefetched.
        """
        return Task.objects.all().select_related('assignee', 'column__board').prefetch_related('reviewers')

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        
        Returns:
            class: TaskUpdateSerializer for update actions, TaskSerializer otherwise.
        """
        if self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        return TaskSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new task.
        
        Args:
            request: HTTP request object containing task data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
            
        Returns:
            Response: HTTP response with created task data or validation errors.
        """
        self._log_request("Task creation", request)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            return self._handle_successful_creation(serializer)
        else:
            return self._handle_validation_error("Task creation", serializer.errors)

    def _log_request(self, action, request):
        """
        Log request information for debugging.
        
        Args:
            action (str): Description of the action being performed.
            request: HTTP request object.
        """
        logger.info(f"{action} request from user: {request.user}")
        logger.info(f"Request data: {request.data}")

    def _handle_successful_creation(self, serializer):
        """
        Handle successful task creation.
        
        Args:
            serializer: Validated serializer instance.
            
        Returns:
            Response: HTTP 201 response with created task data.
        """
        task = serializer.save()
        logger.info(f"Task created successfully: {task.title}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _handle_validation_error(self, action, errors):
        """
        Handle validation errors and log them.
        
        Args:
            action (str): Description of the failed action.
            errors (dict): Validation error details.
            
        Returns:
            Response: HTTP 400 response with error details.
        """
        logger.error(f"{action} failed: {errors}")
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Update an existing task.
        
        Args:
            request: HTTP request object containing updated task data.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
            
        Returns:
            Response: HTTP response with updated task data or validation errors.
        """
        self._log_request("Task update", request)
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            return self._handle_successful_update(serializer)
        else:
            return self._handle_validation_error("Task update", serializer.errors)

    def _handle_successful_update(self, serializer):
        """
        Handle successful task update.
        
        Args:
            serializer: Validated serializer instance.
            
        Returns:
            Response: HTTP 200 response with updated task data.
        """
        task = serializer.save()
        logger.info(f"Task updated successfully: {task.title}")
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a task.
        
        Args:
            request: HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
            
        Returns:
            Response: HTTP 204 response indicating successful deletion.
        """
        logger.info(f"Task deletion request from user: {request.user}")
        instance = self.get_object()
        task_title = instance.title
        self.perform_destroy(instance)
        logger.info(f"Task deleted successfully: {task_title}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def move_to_column(self, request, pk=None):
        """
        Move a task to a different column.
        
        Args:
            request: HTTP request object containing column_id.
            pk (int, optional): Primary key of the task to move.
            
        Returns:
            Response: HTTP response indicating success or failure.
            
        Raises:
            Http404: If task or column is not found.
        """
        self._log_request("Move task", request)
        
        task = self.get_object()
        column_id = request.data.get('column_id')
        
        if not column_id:
            return Response({'error': 'column_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        return self._move_task_to_column(task, column_id)

    def _move_task_to_column(self, task, column_id):
        """
        Move task to specified column.
        
        Args:
            task: Task instance to move.
            column_id (int): ID of target column.
            
        Returns:
            Response: HTTP response indicating success or failure.
        """
        try:
            column = Column.objects.get(id=column_id)
            task.column = column
            task.save()
            logger.info(f"Task moved successfully: {task.title} to column {column.name}")
            return Response({'message': 'Task moved successfully'})
        except Column.DoesNotExist:
            logger.error(f"Column not found: {column_id}")
            return Response({'error': 'Column not found'}, status=status.HTTP_404_NOT_FOUND)