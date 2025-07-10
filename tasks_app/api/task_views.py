from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
import logging

from .serializers import TaskSerializer
from ..models import Task, Comment

logger = logging.getLogger(__name__)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            Q(column__board__owner=user) | 
            Q(column__board__members=user)
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        column = serializer.validated_data.get('column')
        if column:
            if not (column.board.owner == self.request.user or 
                    self.request.user in column.board.members.all()):
                raise PermissionDenied('You do not have permission to create tasks in this board')
        
        task = serializer.save(created_by=self.request.user)
        logger.info(f"Task '{task.title}' created by {self.request.user.username}")

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        task = self.get_object()
        
        if request.method == 'GET':
            comments = task.comments.all().order_by('-created_at')
            serialized_comments = []
            for comment in comments:
                author_name = f"{comment.author.first_name} {comment.author.last_name}".strip() or comment.author.username
                serialized_comments.append({
                    'id': comment.id,
                    'content': comment.content,
                    'author': author_name,
                    'created_at': comment.created_at.isoformat()
                })
            return Response(serialized_comments)
        
        elif request.method == 'POST':
            content = request.data.get('content')
            if not content:
                return Response({'error': 'Content required'}, status=400)
            
            comment = Comment.objects.create(
                task=task,
                author=request.user,
                content=content
            )
            
            author_name = f"{comment.author.first_name} {comment.author.last_name}".strip() or comment.author.username
            return Response({
                'id': comment.id,
                'content': comment.content,
                'author': author_name,
                'created_at': comment.created_at.isoformat()
            }, status=201)

    @action(detail=True, methods=['delete'], url_path='comments/(?P<comment_id>[^/.]+)')
    def delete_comment(self, request, pk=None, comment_id=None):
        try:
            comment = Comment.objects.get(id=comment_id, task_id=pk)
            if comment.author != request.user:
                return Response({'error': 'Permission denied'}, status=403)
            comment.delete()
            return Response(status=204)
        except Comment.DoesNotExist:
            return Response({'error': 'Comment not found'}, status=404)

    @action(detail=False, methods=['get'])
    def assigned_to_me(self, request):
        tasks = self.get_queryset().filter(assignee=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def reviewing(self, request):
        tasks = self.get_queryset().filter(reviewers=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            Q(column__board__owner=user) | 
            Q(column__board__members=user)
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        logger.info(f"Creating task by user: {self.request.user.username}")
        task = serializer.save(created_by=self.request.user)
        logger.info(f"Task '{task.title}' created successfully with ID {task.id}")


class TaskRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            Q(column__board__owner=user) | 
            Q(column__board__members=user)
        ).distinct()

    def perform_update(self, serializer):
        task_id = serializer.instance.id
        old_status = serializer.instance.status
        logger.info(f"Updating task {task_id} by user: {self.request.user.username}")
        
        task = serializer.save()
        
        if 'status' in serializer.validated_data and old_status != task.status:
            logger.info(f"Task {task_id} status changed from '{old_status}' to '{task.status}'")

    def perform_destroy(self, instance):
        task_id = instance.id
        task_title = instance.title
        logger.info(f"Deleting task {task_id} '{task_title}' by user: {self.request.user.username}")
        instance.delete()
        logger.info(f"Task {task_id} successfully deleted")


class TasksAssignedToMeView(generics.ListAPIView):
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(
            assignee=self.request.user
        ).order_by('due_date', '-created_at')


class TasksReviewingView(generics.ListAPIView):
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(
            reviewers=self.request.user
        ).order_by('due_date', '-created_at')