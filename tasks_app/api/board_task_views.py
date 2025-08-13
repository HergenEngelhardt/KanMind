"""
API views for board-related task management.

This module contains views for listing, retrieving, updating, and
deleting tasks within the context of a specific board.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from tasks_app.models import Task
from kanban_app.models import Board, Column
from .serializers import TaskSerializer
from .permissions import IsBoardMember
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

User = get_user_model()


class BoardTaskListView(APIView):
    """
    List all tasks for a specific board.
    
    Requires the user to be a member of the board.
    """
    permission_classes = [IsAuthenticated, IsBoardMember]
    
    def get(self, request, board_id):
        """
        Retrieve all tasks for a specific board.
        
        Args:
            request (Request): The HTTP request.
            board_id (int): The board ID.
            
        Returns:
            Response: List of tasks for the board.
            
        Raises:
            Http404: If board not found.
        """
        board = get_object_or_404(Board, id=board_id)
        self.check_object_permissions(request, board)
        
        columns = Column.objects.filter(board=board)
        tasks = Task.objects.filter(column__in=columns)
        
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class BoardTaskDetailView(APIView):
    """
    Retrieve, update or delete a task within a board context.
    
    Requires the user to be a member of the board.
    """
    permission_classes = [IsAuthenticated, IsBoardMember]
    
    def get(self, request, board_id, pk):
        """
        Retrieve details of a specific task within a board.
        
        Args:
            request (Request): The HTTP request.
            board_id (int): The board ID.
            pk (int): The task ID.
            
        Returns:
            Response: Task data or error.
            
        Raises:
            Http404: If task or board not found.
        """
        board = get_object_or_404(Board, id=board_id)
        self.check_object_permissions(request, board)
        
        task = get_object_or_404(Task, id=pk, column__board=board)
        serializer = TaskSerializer(task)
        return Response(serializer.data)
    
    def patch(self, request, board_id, pk):
        """
        Update a specific task within a board.
        
        Args:
            request (Request): The HTTP request with update data.
            board_id (int): The board ID.
            pk (int): The task ID.
            
        Returns:
            Response: Updated task data or error.
            
        Raises:
            Http404: If task or board not found.
        """
        board = get_object_or_404(Board, id=board_id)
        self.check_object_permissions(request, board)
        
        task = get_object_or_404(Task, id=pk, column__board=board)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        
        if serializer.is_valid():
            updated_task = serializer.save()
            
            reviewer_id = request.data.get('reviewer_id')
            self._update_reviewer_if_provided(updated_task, reviewer_id)
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _update_reviewer_if_provided(self, task, reviewer_id):
        """
        Update the task reviewer if provided in request.
        
        Args:
            task (Task): The task to update reviewer for.
            reviewer_id (int): The ID of the reviewer.
        """
        if reviewer_id is not None:
            try:
                reviewer = User.objects.get(id=reviewer_id)
                task.reviewer.clear()
                task.reviewer.add(reviewer)
            except User.DoesNotExist:
                pass
    
    def delete(self, request, board_id, pk):
        """
        Delete a specific task within a board.
        
        Args:
            request (Request): The HTTP request.
            board_id (int): The board ID.
            pk (int): The task ID.
            
        Returns:
            Response: Empty response on success.
            
        Raises:
            Http404: If task or board not found.
            PermissionDenied: If user doesn't have delete permission.
        """
        board = get_object_or_404(Board, id=board_id)
        self.check_object_permissions(request, board)
        
        task = get_object_or_404(Task, id=pk, column__board=board)
        
        if board.owner == request.user or task.created_by == request.user:
            task.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        raise PermissionDenied("You don't have permission to delete this task")