"""
API views for task management.

This module contains views for listing, creating, retrieving,
updating and deleting tasks.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from tasks_app.models import Task
from kanban_app.models import Board, Column
from .serializers import TaskSerializer
from .permissions import IsBoardMember
from django.shortcuts import get_object_or_404


class AssignedTasksView(APIView):
    """
    List all tasks assigned to the current user.
    
    Returns tasks from all boards where the user is assigned as the task assignee.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Retrieve all tasks assigned to the current user.
        
        Args:
            request (Request): The HTTP request object.
            
        Returns:
            Response: A response containing a list of tasks.
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
        Retrieve all tasks where the current user is a reviewer.
        
        Args:
            request (Request): The HTTP request object.
            
        Returns:
            Response: A response containing a list of tasks.
        """
        tasks = Task.objects.filter(reviewers=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class TaskListCreateView(APIView):
    """
    List and create tasks for a specific board.
    
    Requires the user to be a member of the board.
    """
    permission_classes = [IsAuthenticated, IsBoardMember]
    
    def get_board(self, board_id):
        """
        Retrieve the board based on the provided ID.
        
        Args:
            board_id (int): The ID of the board.
            
        Returns:
            Board: The board object.
            
        Raises:
            Http404: If the board doesn't exist.
        """
        return get_object_or_404(Board, pk=board_id)
        
    def get(self, request, board_id):
        """
        Retrieve all tasks for the specified board.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            
        Returns:
            Response: A response containing a list of tasks.
        """
        board = self.get_board(board_id)
        self.check_object_permissions(request, board)
        
        columns = board.columns.all()
        tasks = Task.objects.filter(column__in=columns)
        
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    def post(self, request, board_id):
        """
        Create a new task in the specified board.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            
        Returns:
            Response: A response containing the created task data.
            
        Raises:
            ValidationError: If the request data is invalid.
        """
        board = self.get_board(board_id)
        self.check_object_permissions(request, board)
        
        column_id = self._get_column_id(request.data, board)
        if not column_id:
            return Response(
                {"detail": "Board has no columns. Create a column first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = self._prepare_task_data(request.data, column_id)
        serializer = TaskSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_column_id(self, data, board):
        """
        Get the column ID for a new task.
        
        Args:
            data (dict): The request data.
            board (Board): The board object.
            
        Returns:
            int: The column ID or None if no column exists.
        """
        column_id = data.get('column')
        if column_id:
            if board.columns.filter(id=column_id).exists():
                return column_id
                
        column = board.columns.first()
        return column.id if column else None
    
    def _prepare_task_data(self, data, column_id):
        """
        Prepare the task data for serialization.
        
        Args:
            data (dict): The original request data.
            column_id (int): The column ID to use.
            
        Returns:
            dict: The prepared task data.
        """
        data_copy = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'board' in data_copy:
            data_copy.pop('board')
        data_copy['column'] = column_id
        return data_copy


class TaskDetailView(APIView):
    """
    Retrieve, update or delete a task.
    
    Requires the user to be a member of the board that the task belongs to.
    """
    permission_classes = [IsAuthenticated, IsBoardMember]
    
    def get_board_and_task(self, board_id, pk):
        """
        Retrieve a board and task based on their IDs.
        
        Args:
            board_id (int): The ID of the board.
            pk (int): The ID of the task.
            
        Returns:
            tuple: A tuple containing (board, task).
            
        Raises:
            Http404: If the board or task doesn't exist or if the task doesn't belong to the board.
        """
        board = get_object_or_404(Board, pk=board_id)
        columns = board.columns.values_list('id', flat=True)
        task = get_object_or_404(Task, pk=pk, column__in=columns)
        return board, task
    
    def get(self, request, board_id, pk):
        """
        Retrieve a specific task.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            pk (int): The ID of the task.
            
        Returns:
            Response: A response containing the task data.
        """
        board, task = self.get_board_and_task(board_id, pk)
        self.check_object_permissions(request, board)
        
        serializer = TaskSerializer(task)
        return Response(serializer.data)
    
    def patch(self, request, board_id, pk):
        """
        Update a specific task.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            pk (int): The ID of the task.
            
        Returns:
            Response: A response containing the updated task data.
            
        Raises:
            ValidationError: If the request data is invalid.
        """
        board, task = self.get_board_and_task(board_id, pk)
        self.check_object_permissions(request, board)
        
        if self._column_change_is_invalid(request.data, board):
            return Response(
                {"detail": "Column does not belong to this board"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _column_change_is_invalid(self, data, board):
        """
        Check if a column change is invalid.
        
        Args:
            data (dict): The request data.
            board (Board): The board object.
            
        Returns:
            bool: True if the column change is invalid, False otherwise.
        """
        if 'column' not in data:
            return False
            
        return not board.columns.filter(id=data['column']).exists()
    
    def delete(self, request, board_id, pk):
        """
        Delete a specific task.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            pk (int): The ID of the task.
            
        Returns:
            Response: An empty response with 204 status code.
        """
        board, task = self.get_board_and_task(board_id, pk)
        self.check_object_permissions(request, board)
        
        if not self._can_delete_task(request.user, task, board):
            return Response(
                {"detail": "Only task creator or board owner can delete tasks"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def _can_delete_task(self, user, task, board):
        """
        Check if the user can delete the task.
        
        Args:
            user (User): The user attempting to delete the task.
            task (Task): The task to be deleted.
            board (Board): The board containing the task.
            
        Returns:
            bool: True if the user can delete the task, False otherwise.
        """
        return task.created_by == user or board.owner == user