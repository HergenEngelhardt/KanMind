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
    
    Returns tasks from all boards where the user is assigned.
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


class TaskCreateView(APIView):
    """
    Create a new task for a specific board.
    
    Requires the user to be a member of the board.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Create a new task with board ID provided in the request data.
        
        Args:
            request (Request): The HTTP request object.
            
        Returns:
            Response: A response containing the created task data.
            
        Raises:
            ValidationError: If the request data is invalid.
        """
        board_id = request.data.get('board')
        if not board_id:
            return Response(
                {"detail": "Board ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            board = self._get_board_or_404(board_id)
            self._check_board_membership(request, board)
            
            column = self._get_or_create_column(board)
            
            data = request.data.copy()
            serializer = TaskSerializer(data=data, context={'request': request})
            
            if serializer.is_valid():
                task = serializer.save(created_by=request.user, column=column)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Board.DoesNotExist:
            return Response(
                {"detail": f"Board with id {board_id} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _get_board_or_404(self, board_id):
        """
        Get a board by ID or return 404.
        
        Args:
            board_id (int): The board ID.
            
        Returns:
            Board: The board object.
            
        Raises:
            Http404: If the board doesn't exist.
        """
        return get_object_or_404(Board, pk=board_id)
    
    def _check_board_membership(self, request, board):
        """
        Check if the user is a member of the board.
        
        Args:
            request (Request): The HTTP request.
            board (Board): The board to check.
            
        Raises:
            PermissionDenied: If the user is not a board member.
        """
        permission = IsBoardMember()
        if not permission.has_object_permission(request, self, board):
            self.permission_denied(request)
    
    def _get_or_create_column(self, board):
        """
        Get or create a default column for a board.
        
        Args:
            board (Board): The board to get a column for.
            
        Returns:
            Column: A column object.
        """
        columns = board.columns.all()
        if columns.exists():
            return columns.first()
        
        return Column.objects.create(
            board=board,
            title="To Do",
            position=0
        )


class TaskDetailView(APIView):
    """
    Retrieve, update or delete a task.
    
    Requires the user to be a member of the board that the task belongs to.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """
        Retrieve a specific task.
        
        Args:
            request (Request): The HTTP request object.
            pk (int): The ID of the task.
            
        Returns:
            Response: A response containing the task data.
        """
        task = self._get_task_or_404(pk)
        board = task.column.board
        self._check_board_membership(request, board)
        
        serializer = TaskSerializer(task)
        return Response(serializer.data)
    
    def patch(self, request, pk):
        """
        Update a specific task.
        
        Args:
            request (Request): The HTTP request object.
            pk (int): The ID of the task.
            
        Returns:
            Response: A response containing the updated task data.
            
        Raises:
            ValidationError: If the request data is invalid.
        """
        try:
            task = self._get_task_or_404(pk)
            board = task.column.board
            self._check_board_membership(request, board)
            
            data = request.data.copy()
            if 'board' in data:
                data.pop('board')  
            
            serializer = TaskSerializer(task, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Task.DoesNotExist:
            return Response(
                {"detail": f"Task with id {pk} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, pk):
        """
        Delete a specific task.
        
        Args:
            request (Request): The HTTP request object.
            pk (int): The ID of the task.
            
        Returns:
            Response: An empty response with 204 status code.
        """
        task = self._get_task_or_404(pk)
        board = task.column.board
        self._check_board_membership(request, board)
        
        if not self._can_delete_task(request.user, task, board):
            return Response(
                {"detail": "Only task creator or board owner can delete tasks"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def _get_task_or_404(self, task_id):
        """
        Get a task by ID or return 404.
        
        Args:
            task_id (int): The task ID.
            
        Returns:
            Task: The task object.
            
        Raises:
            Http404: If the task doesn't exist.
        """
        return get_object_or_404(Task, pk=task_id)
    
    def _check_board_membership(self, request, board):
        """
        Check if the user is a member of the board.
        
        Args:
            request (Request): The HTTP request.
            board (Board): The board to check.
            
        Raises:
            PermissionDenied: If the user is not a board member.
        """
        permission = IsBoardMember()
        if not permission.has_object_permission(request, self, board):
            self.permission_denied(request)
    
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


class BoardTaskListView(APIView):
    """
    List and create tasks for a specific board.
    
    Requires the user to be a member of the board.
    """
    permission_classes = [IsAuthenticated, IsBoardMember]
    
    def get(self, request, board_id):
        """
        Retrieve all tasks for the specified board.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            
        Returns:
            Response: A response containing a list of tasks.
        """
        try:
            board = self._get_board_or_404(board_id)
            self.check_object_permissions(request, board)
            
            tasks = self._get_tasks_for_board(board)
            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)
        except Board.DoesNotExist:
            return Response(
                {"detail": f"Board with id {board_id} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
    
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
        try:
            board = self._get_board_or_404(board_id)
            self.check_object_permissions(request, board)
            
            column = self._get_or_create_column(board)
            
            data = self._prepare_task_data(request.data, column.id, board_id)
            serializer = TaskSerializer(data=data, context={'request': request})
            
            if serializer.is_valid():
                task = serializer.save(created_by=request.user, column=column)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Board.DoesNotExist:
            return Response(
                {"detail": f"Board with id {board_id} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _get_board_or_404(self, board_id):
        """
        Get a board by ID or return 404.
        
        Args:
            board_id (int): The board ID.
            
        Returns:
            Board: The board object.
            
        Raises:
            Http404: If the board doesn't exist.
        """
        return get_object_or_404(Board, pk=board_id)
    
    def _get_tasks_for_board(self, board):
        """
        Get all tasks associated with a board.
        
        Args:
            board (Board): The board object.
            
        Returns:
            QuerySet: The tasks associated with the board.
        """
        columns = board.columns.all()
        return Task.objects.filter(column__in=columns)
    
    def _get_or_create_column(self, board):
        """
        Get or create a default column for a board.
        
        Args:
            board (Board): The board to get a column for.
            
        Returns:
            Column: A column object.
        """
        columns = board.columns.all()
        if columns.exists():
            return columns.first()
        
        return Column.objects.create(
            board=board,
            title="To Do",
            position=0
        )
    
    def _prepare_task_data(self, data, column_id, board_id):
        """
        Prepare task data for serialization.
        
        Args:
            data (dict): The request data.
            column_id (int): The ID of the column.
            board_id (int): The ID of the board.
            
        Returns:
            dict: The prepared task data.
        """
        task_data = data.copy() if isinstance(data, dict) else {}
        task_data['column'] = column_id
        task_data['board'] = board_id
        return task_data


class BoardTaskDetailView(APIView):
    """
    Retrieve, update or delete a task within a board context.
    
    Requires the user to be a member of the board that the task belongs to.
    """
    permission_classes = [IsAuthenticated, IsBoardMember]
    
    def get(self, request, board_id, pk):
        """
        Retrieve a specific task in a board.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            pk (int): The ID of the task.
            
        Returns:
            Response: A response containing the task data.
        """
        try:
            board, task = self._get_board_and_task(board_id, pk)
            self.check_object_permissions(request, board)
            
            serializer = TaskSerializer(task)
            return Response(serializer.data)
        except Board.DoesNotExist:
            return Response(
                {"detail": f"Board with id {board_id} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Task.DoesNotExist:
            return Response(
                {"detail": f"Task with id {pk} does not exist or doesn't belong to this board"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request, board_id, pk):
        """
        Update a specific task in a board.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            pk (int): The ID of the task.
            
        Returns:
            Response: A response containing the updated task data.
            
        Raises:
            ValidationError: If the request data is invalid.
        """
        try:
            if pk == 'null' or pk is None:
                return Response(
                    {"detail": "Invalid task ID: must be a number"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            board, task = self._get_board_and_task(board_id, pk)
            self.check_object_permissions(request, board)
            
            if self._column_change_is_invalid(request.data, board):
                return Response(
                    {"detail": "Column does not belong to this board"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = request.data.copy()
            if 'board' in data:
                data.pop('board')  
                
            serializer = TaskSerializer(task, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response(
                {"detail": "Invalid task ID format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Board.DoesNotExist:
            return Response(
                {"detail": f"Board with id {board_id} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Task.DoesNotExist:
            return Response(
                {"detail": f"Task with id {pk} does not exist or doesn't belong to this board"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, board_id, pk):
        """
        Delete a specific task in a board.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            pk (int): The ID of the task.
            
        Returns:
            Response: An empty response with 204 status code.
        """
        try:
            board, task = self._get_board_and_task(board_id, pk)
            self.check_object_permissions(request, board)
            
            if not self._can_delete_task(request.user, task, board):
                return Response(
                    {"detail": "Only task creator or board owner can delete tasks"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            task.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Board.DoesNotExist:
            return Response(
                {"detail": f"Board with id {board_id} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Task.DoesNotExist:
            return Response(
                {"detail": f"Task with id {pk} does not exist or doesn't belong to this board"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _get_board_and_task(self, board_id, pk):
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