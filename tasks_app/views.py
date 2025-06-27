from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Task, Comment
from tasks_app.api.serializers import TaskSerializer, CommentSerializer
from kanban_app.api.permissions import IsOwnerOrReadOnly


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks.
    
    Provides CRUD operations for tasks with proper permissions.
    Includes custom actions for assigned and reviewing tasks.
    """
    
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """
        Return tasks that the user has access to.
        
        Users can see tasks in boards they own or are members of.
        """
        user = self.request.user
        return Task.objects.filter(
            Q(column__board__owner=user) | 
            Q(column__board__members=user)
        ).distinct()

    def perform_create(self, serializer):
        """
        Create task with validation.
        
        Ensures user has permission to create tasks in the specified column.
        """
        column = serializer.validated_data['column']
        if not (column.board.owner == self.request.user or 
                self.request.user in column.board.members.all()):
            raise PermissionDenied('Permission denied')
        serializer.save()

    @action(detail=False, methods=['get'])
    def assigned_to_me(self, request):
        """Get tasks assigned to the current user."""
        tasks = self.get_queryset().filter(assignee=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def reviewing(self, request):
        """Get tasks where current user is a reviewer."""
        tasks = self.get_queryset().filter(reviewers=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class CommentListCreateView(generics.ListCreateAPIView):
    """
    List comments for a task or create a new comment.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Get comments for specific task."""
        task_id = self.kwargs['task_id']
        return Comment.objects.filter(task_id=task_id).order_by('-created_at')

    def perform_create(self, serializer):
        """Create comment for specific task."""
        task_id = self.kwargs['task_id']
        task = get_object_or_404(Task, id=task_id)
        
        # Check if user has permission to comment on this task
        if not (task.column.board.owner == self.request.user or 
                self.request.user in task.column.board.members.all()):
            raise PermissionDenied('Permission denied')
        
        serializer.save(task=task, author=self.request.user)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a comment.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Get comments for specific task."""
        task_id = self.kwargs['task_id']
        return Comment.objects.filter(task_id=task_id)

    def get_object(self):
        """Get specific comment."""
        queryset = self.get_queryset()
        pk = self.kwargs.get('pk')
        return get_object_or_404(queryset, pk=pk)