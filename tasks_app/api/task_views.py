from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from tasks_app.models import Task
from kanban_app.models import Column
from .serializers import TaskSerializer

class TaskListCreate(generics.ListCreateAPIView):
    """List tasks for a column or create a new task."""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        column_id = self.request.query_params.get('column_id')
        if column_id:
            return Task.objects.filter(column_id=column_id).order_by('position')
        return Task.objects.none()

    def perform_create(self, serializer):
        column_id = self.request.data.get('column_id')
        column = get_object_or_404(Column, id=column_id)
        
        # Set position as the last in the column
        last_position = Task.objects.filter(column=column).count()
        serializer.save(column=column, position=last_position + 1)

class TaskRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a task."""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()

class TasksAssignedToMeView(generics.ListAPIView):
    """List tasks assigned to the current user."""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user).order_by('-created_at')

class TasksReviewingView(generics.ListAPIView):
    """List tasks where the current user is a reviewer."""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(reviewers=self.request.user).order_by('-created_at')