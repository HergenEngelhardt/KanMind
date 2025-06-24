from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.db import models
from django.shortcuts import get_object_or_404
from tasks_app.models import Task, Comment
from kanban_app.models import Column
from .serializers import TaskSerializer, CommentSerializer


class TaskListCreate(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        column_id = self.request.query_params.get("column", None)
        if column_id:
            return Task.objects.filter(column_id=column_id)
        return Task.objects.filter(column__board__owner=self.request.user)

    def perform_create(self, serializer):
        column_id = self.request.data.get("column")
        try:
            column = Column.objects.get(id=column_id)
            if column.board.owner != self.request.user:
                raise PermissionDenied(
                    "You don't have permission to add tasks to this column"
                )
            serializer.save(column=column)
        except Column.DoesNotExist:
            raise PermissionDenied("Column does not exist")


class TaskRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(
            models.Q(column__board__owner=self.request.user)
            | models.Q(column__board__members=self.request.user)
        ).distinct()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
        
    def partial_update(self, request, *args, **kwargs):
        try:
            return super().partial_update(request, *args, **kwargs)
        except Exception as e:
            print(f"Error updating task: {str(e)}")
            return Response(
                {"error": "Ein Fehler ist beim Aktualisieren der Aufgabe aufgetreten."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TasksAssignedToMeView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)


class TasksReviewingView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(reviewers=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        task_id = self.kwargs.get("task_id")
        task = get_object_or_404(Task, id=task_id)

        board = task.column.board
        if not (
            board.owner == self.request.user or self.request.user in board.members.all()
        ):
            raise PermissionDenied(
                "You don't have permission to view comments for this task"
            )

        return Comment.objects.filter(task_id=task_id)

    def perform_create(self, serializer):
        task_id = self.kwargs.get("task_id")
        task = get_object_or_404(Task, id=task_id)

        board = task.column.board
        if not (
            board.owner == self.request.user or self.request.user in board.members.all()
        ):
            raise PermissionDenied("You don't have permission to comment on this task")

        serializer.save(task=task, author=self.request.user)


class CommentDeleteView(generics.DestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        task_id = self.kwargs.get("task_id")
        return Comment.objects.filter(task_id=task_id)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()

        task = comment.task
        if not (
            comment.author == request.user or task.column.board.owner == request.user
        ):
            raise PermissionDenied("You don't have permission to delete this comment")

        return super().destroy(request, *args, **kwargs)
