"""
API views for task management.

This module contains views for listing, creating, retrieving,
updating and deleting tasks.
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

class AssignedTasksView(APIView):
    """
    List all tasks assigned to the current user.
    
    Returns tasks from all boards where the user is assigned.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Retrieve all tasks assigned to the authenticated user.
        
        Args:
            request (Request): The HTTP request object
            
        Returns:
            Response: List of tasks where the user is the assignee
        """
        tasks = Task.objects.filter(assignee=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class ReviewingTasksView(APIView):
    """
    List all tasks where the current user is set as reviewer.
    
    Returns tasks from all boards where the user is assigned as a reviewer.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Retrieve all tasks where the authenticated user is a reviewer.
        
        Args:
            request (Request): The HTTP request object
            
        Returns:
            Response: List of tasks where the user is a reviewer
        """
        tasks = Task.objects.filter(reviewer=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class TaskCreateView(APIView):
    """
    Create a new task for a specific board.
    
    Requires the user to be a member of the board.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Create a new task for a board.
        
        Args:
            request (Request): HTTP request with task data
            
        Returns:
            Response: Created task data or error messages
            
        Raises:
            Http404: If board not found
        """
        board_id = request.data.get('board')
        board = self._get_board_or_404(board_id)
        
        self._check_board_membership(request, board)
        
        column = self._get_or_create_column(board)
        
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user, column=column)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_board_or_404(self, board_id):
        """
        Get board by ID or raise 404.
        
        Args:
            board_id (int): The board ID
            
        Returns:
            Board: The board instance
            
        Raises:
            Http404: If board not found
        """
        return get_object_or_404(Board, id=board_id)
    
    def _check_board_membership(self, request, board):
        """
        Check if user is a member of the board.
        
        Args:
            request (Request): The HTTP request
            board (Board): The board to check
            
        Raises:
            PermissionDenied: If user is not a board member
        """
        if not (board.owner == request.user or board.members.filter(
                id=request.user.id).exists()):
            raise PermissionDenied("You are not a member of this board")
    
    def _get_or_create_column(self, board):
        """
        Get first column or create default column.
        
        Args:
            board (Board): The board to get/create column for
            
        Returns:
            Column: A column instance
        """
        column = Column.objects.filter(board=board).first()
        if not column:
            column = Column.objects.create(
                board=board,
                title="To Do",
                position=0
            )
        return column


class TaskDetailView(APIView):
    """
    Retrieve, update or delete a task.
    
    Requires the user to be a member of the board that the task belongs to.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """
        Retrieve details of a specific task.
        
        Args:
            request (Request): The HTTP request
            pk (int): The task ID
            
        Returns:
            Response: Task data or error
            
        Raises:
            Http404: If task not found
        """
        task = self._get_task_or_404(pk)
        self._check_board_membership(request, task.column.board)
        
        serializer = TaskSerializer(task)
        return Response(serializer.data)
    
    def patch(self, request, pk):
        """
        Update a specific task.
        
        Args:
            request (Request): The HTTP request with update data
            pk (int): The task ID
            
        Returns:
            Response: Updated task data or error
            
        Raises:
            Http404: If task not found
        """
        task = self._get_task_or_404(pk)
        self._check_board_membership(request, task.column.board)
        
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """
        Delete a specific task.
        
        Args:
            request (Request): The HTTP request
            pk (int): The task ID
            
        Returns:
            Response: Empty response on success
            
        Raises:
            Http404: If task not found
            PermissionDenied: If user doesn't have delete permission
        """
        task = self._get_task_or_404(pk)
        board = task.column.board
        
        self._check_board_membership(request, board)
        
        if board.owner == request.user or task.created_by == request.user:
            task.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        raise PermissionDenied("You don't have permission to delete this task")
    
    def _get_task_or_404(self, task_id):
        """
        Get task by ID or raise 404.
        
        Args:
            task_id (int): The task ID
            
        Returns:
            Task: The task instance
            
        Raises:
            Http404: If task not found
        """
        return get_object_or_404(Task, id=task_id)
    
    def _check_board_membership(self, request, board):
        """
        Check if user is a member of the board.
        
        Args:
            request (Request): The HTTP request
            board (Board): The board to check
            
        Raises:
            PermissionDenied: If user is not a board member
        """
        if not (board.owner == request.user or board.members.filter(
                id=request.user.id).exists()):
            raise PermissionDenied("You are not a member of this board")


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
            request (Request): The HTTP request
            board_id (int): The board ID
            
        Returns:
            Response: List of tasks for the board
            
        Raises:
            Http404: If board not found
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
            request (Request): The HTTP request
            board_id (int): The board ID
            pk (int): The task ID
            
        Returns:
            Response: Task data or error
            
        Raises:
            Http404: If task or board not found
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
            request (Request): The HTTP request with update data
            board_id (int): The board ID
            pk (int): The task ID
            
        Returns:
            Response: Updated task data or error
            
        Raises:
            Http404: If task or board not found
        """
        board = get_object_or_404(Board, id=board_id)
        self.check_object_permissions(request, board)
        
        task = get_object_or_404(Task, id=pk, column__board=board)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, board_id, pk):
        """
        Delete a specific task within a board.
        
        Args:
            request (Request): The HTTP request
            board_id (int): The board ID
            pk (int): The task ID
            
        Returns:
            Response: Empty response on success
            
        Raises:
            Http404: If task or board not found
            PermissionDenied: If user doesn't have delete permission
        """
        board = get_object_or_404(Board, id=board_id)
        self.check_object_permissions(request, board)
        
        task = get_object_or_404(Task, id=pk, column__board=board)
        
        if board.owner == request.user or task.created_by == request.user:
            task.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        raise PermissionDenied("You don't have permission to delete this task")