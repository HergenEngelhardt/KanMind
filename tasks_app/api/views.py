from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import Task
from .serializers import TaskSerializer
from kanban_app.models import Column


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Task CRUD operations.
    
    Provides complete task management functionality including creation,
    retrieval, updating, and deletion with user-specific filtering.
    """
    
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get the queryset of all tasks with related data.
        
        Returns:
            QuerySet: All tasks with prefetched assignee, column, board, and reviewers
        """
        return Task.objects.all().select_related(
            'assignee', 'column__board'
        ).prefetch_related('reviewers')

    @action(detail=False, methods=['get'])
    def assigned_to_me(self, request):
        """
        Get tasks assigned to the current user.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Serialized list of tasks assigned to current user
        """
        tasks = self._get_user_assigned_tasks(request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    def _get_user_assigned_tasks(self, user):
        """
        Retrieve tasks assigned to a specific user.
        
        Args:
            user (User): User to filter tasks by
            
        Returns:
            QuerySet: Tasks assigned to the user with related data
        """
        return Task.objects.filter(assignee=user).select_related(
            'column__board', 'created_by', 'assignee'
        ).prefetch_related('reviewers')

    @action(detail=False, methods=['get'])
    def reviewing(self, request):
        """
        Get tasks being reviewed by the current user.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Serialized list of tasks being reviewed by current user
        """
        tasks = self._get_user_reviewing_tasks(request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    def _get_user_reviewing_tasks(self, user):
        """
        Retrieve tasks being reviewed by a specific user.
        
        Args:
            user (User): User to filter tasks by
            
        Returns:
            QuerySet: Tasks being reviewed by the user with related data
        """
        return Task.objects.filter(reviewers=user).select_related(
            'column__board', 'created_by', 'assignee'
        ).prefetch_related('reviewers')