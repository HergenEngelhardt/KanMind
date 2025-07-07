import logging
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from django.db import models
from django.db.models import Q
from tasks_app.models import Task
from kanban_app.models import Column, Board
from .serializers import TaskSerializer
from .permissions import (
    IsTaskBoardMember, 
    IsTaskAssigneeOrBoardOwner
)


class TaskListCreate(generics.ListCreateAPIView):
    """
    List tasks or create a new task.
    
    GET: Returns tasks filtered by column or user's boards
    POST: Creates a new task in specified column with permission check
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return tasks filtered by column or user's boards."""
        column_id = self.request.query_params.get("column")
        if column_id:
            if not column_id.isdigit():
                raise ValidationError("Invalid column ID")
            return Task.objects.filter(column_id=column_id)
        return self._get_user_board_tasks()

    def _get_user_board_tasks(self):
        """Get tasks from boards where user is owner or member."""
        user_boards = Board.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).distinct()
        return Task.objects.filter(column__board__in=user_boards)

    def perform_create(self, serializer):
        """Ensure the user has permission to create tasks in the specified column."""
        column = serializer.validated_data['column']
        board = column.board
        
        if not (board.owner == self.request.user or self.request.user in board.members.all()):
            raise PermissionDenied("You don't have permission to create tasks in this board.")
        
        serializer.save()


class TaskRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific task.
    
    Different permission classes based on request method.
    Update requires assignee or board owner permissions.
    """
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskBoardMember]

    def get_permissions(self):
        """Set permissions based on request method."""
        if self.request.method in ['PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsTaskAssigneeOrBoardOwner()]
        return [permissions.IsAuthenticated(), IsTaskBoardMember()]

    def get_queryset(self):
        """Return tasks from user's boards (owned or member)."""
        return Task.objects.filter(
            models.Q(column__board__owner=self.request.user)
            | models.Q(column__board__members=self.request.user)
        ).distinct()
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
        
    def partial_update(self, request, *args, **kwargs):
        """Handle partial task update with error handling."""
        try:
            return super().partial_update(request, *args, **kwargs)
        except Exception as e:
            return self._update_error_response()

    def _update_error_response(self):
        """Return error response for update failures."""
        return Response(
            {"error": "An error occurred while updating the task."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class TasksAssignedToMeView(generics.ListAPIView):
    """
    List tasks assigned to the current user.
    
    Returns all tasks where the authenticated user is the assignee.
    """
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return tasks assigned to current user."""
        return Task.objects.filter(assignee=self.request.user)


class TasksReviewingView(generics.ListAPIView):
    """
    List tasks being reviewed by the current user.
    
    Returns all tasks where the authenticated user is a reviewer.
    """
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return tasks being reviewed by current user."""
        return Task.objects.filter(reviewers=self.request.user)