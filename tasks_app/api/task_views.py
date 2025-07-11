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
from ..models import Task

logger = logging.getLogger(__name__)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Task.objects.filter(
            Q(column__board__boardmembership__user=self.request.user) |
            Q(assignee=self.request.user) |
            Q(reviewers=self.request.user)
        ).select_related(
            'assignee', 'column', 'column__board', 'created_by'
        ).prefetch_related('reviewers').distinct()
        
        board_id = self.request.query_params.get('board', None)
        if board_id:
            queryset = queryset.filter(column__board_id=board_id)
            
        return queryset

    def perform_create(self, serializer):
        board_id = self.request.data.get('board')
        if board_id:
            from kanban_app.models import Board
            try:
                board = Board.objects.get(id=board_id)
                if not board.boardmembership_set.filter(user=self.request.user).exists() and board.owner != self.request.user:
                    raise PermissionError("You don't have permission to create tasks on this board")
            except Board.DoesNotExist:
                raise ValueError("Board not found")
        
        serializer.save()

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except (PermissionError, ValueError) as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Task creation error: {str(e)}")
            return Response(
                {"error": "Could not create task"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        try:
            tasks = Task.objects.filter(
                assignee=request.user
            ).select_related(
                'assignee', 'column', 'column__board', 'created_by'
            ).prefetch_related('reviewers')
            
            serializer = self.get_serializer(tasks, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Assigned tasks error: {str(e)}")
            return Response(
                {"error": "Could not fetch assigned tasks"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing(self, request):
        try:
            tasks = Task.objects.filter(
                reviewers=request.user
            ).select_related(
                'assignee', 'column', 'column__board', 'created_by'
            ).prefetch_related('reviewers')
            
            serializer = self.get_serializer(tasks, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Reviewing tasks error: {str(e)}")
            return Response(
                {"error": "Could not fetch reviewing tasks"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )