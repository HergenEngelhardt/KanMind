from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import logging

from ..models import Task
from .serializers import TaskSerializer, TaskUpdateSerializer
from kanban_app.models import Board, BoardMembership

logger = logging.getLogger(__name__)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.all().select_related('assignee', 'column__board').prefetch_related('reviewers')

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        return TaskSerializer

    def create(self, request, *args, **kwargs):
        logger.info(f"Task creation request from user: {request.user}")
        logger.info(f"Request data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save()
            logger.info(f"Task created successfully: {task.title}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"Task creation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        logger.info(f"Task update request from user: {request.user}")
        logger.info(f"Request data: {request.data}")
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            task = serializer.save()
            logger.info(f"Task updated successfully: {task.title}")
            return Response(serializer.data)
        else:
            logger.error(f"Task update failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        logger.info(f"Task deletion request from user: {request.user}")
        instance = self.get_object()
        task_title = instance.title
        self.perform_destroy(instance)
        logger.info(f"Task deleted successfully: {task_title}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def move_to_column(self, request, pk=None):
        logger.info(f"Move task request from user: {request.user}")
        logger.info(f"Request data: {request.data}")
        
        task = self.get_object()
        column_id = request.data.get('column_id')
        
        if not column_id:
            return Response({'error': 'column_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from kanban_app.models import Column
        try:
            column = Column.objects.get(id=column_id)
            task.column = column
            task.save()
            logger.info(f"Task moved successfully: {task.title} to column {column.name}")
            return Response({'message': 'Task moved successfully'})
        except Column.DoesNotExist:
            logger.error(f"Column not found: {column_id}")
            return Response({'error': 'Column not found'}, status=status.HTTP_404_NOT_FOUND)