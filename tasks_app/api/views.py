from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from django.db import models
from tasks_app.models import Task
from .serializers import TaskSerializer
from kanban_app.models import Board, Column


class TaskListCreate(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        column_id = self.request.query_params.get('column', None)
        if column_id:
            return Task.objects.filter(column_id=column_id)
        return Task.objects.filter(column__board__owner=self.request.user)

    def perform_create(self, serializer):
        column_id = self.request.data.get('column')
        try:
            column = Column.objects.get(id=column_id)
            if column.board.owner != self.request.user:
                raise PermissionDenied(
                    "You don't have permission to add tasks to this column")
            serializer.save(column=column)
        except Column.DoesNotExist:
            raise PermissionDenied("Column does not exist")

class TaskRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(
            models.Q(column__board__owner=self.request.user) | 
            models.Q(column__board__members=self.request.user)
        ).distinct()

