from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from tasks_app.models import Task, Comment
from kanban_app.models import Board, BoardMembership, Column
from .serializers import TaskSerializer
from django.shortcuts import get_object_or_404

class AssignedTasksView(APIView):
    """
    View for listing tasks assigned to current user.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Lists tasks assigned to current user.
        
        Args:
            request (Request): HTTP request
            
        Returns:
            Response: JSON list of assigned tasks
        """
        tasks = Task.objects.filter(assignee=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewingTasksView(APIView):
    """
    View for listing tasks user is reviewing.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Lists tasks the current user is reviewing.
        
        Args:
            request (Request): HTTP request
            
        Returns:
            Response: JSON list of tasks to review
        """
        tasks = Task.objects.filter(reviewers=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskCreateView(APIView):
    """
    View for creating tasks in a board.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, board_id):
        """
        Creates a new task in specified board.
        
        Args:
            request (Request): HTTP request with task data
            board_id (int): ID of board for new task
            
        Returns:
            Response: JSON with created task or errors
            
        Raises:
            Http404: If board not found
        """
        serializer = TaskSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            board = Board.objects.get(id=board_id)
        except Board.DoesNotExist:
            return Response(
                {'error': 'Board not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not self._user_has_board_access(board, request.user):
            return Response(
                {'error': 'No permission to create tasks in this board'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not self._validate_assignee_reviewer(request.data, board):
            return Response(
                {'error': 'Assignee and reviewer must be board members'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find or create default column
        default_column = self._get_or_create_default_column(board)
        
        # Create task with board reference
        task = serializer.save(
            column=default_column,
            board=board,
            created_by=request.user
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _user_has_board_access(self, board, user):
        """
        Checks if user has access to board.
        
        Args:
            board (Board): Board instance
            user (User): User to check
            
        Returns:
            bool: True if user has access
        """
        return (board.owner == user or 
                BoardMembership.objects.filter(board=board, user=user).exists())
    
    def _validate_assignee_reviewer(self, data, board):
        """
        Validates assignee and reviewer are board members.
        
        Args:
            data (dict): Request data
            board (Board): Board instance
            
        Returns:
            bool: True if valid
        """
        assignee_id = data.get('assignee_id')
        reviewer_id = data.get('reviewer_id')
        
        if assignee_id and not self._is_board_member(board, assignee_id):
            return False
        
        if reviewer_id and not self._is_board_member(board, reviewer_id):
            return False
        
        return True
    
    def _is_board_member(self, board, user_id):
        """
        Checks if user is board member.
        
        Args:
            board (Board): Board instance
            user_id (int): User ID to check
            
        Returns:
            bool: True if user is member
        """
        return (BoardMembership.objects.filter(
            board=board, user__id=user_id
        ).exists() or board.owner.id == user_id)
        
    def _get_or_create_default_column(self, board):
        """
        Gets or creates default column for task.
        
        Args:
            board (Board): Board instance
            
        Returns:
            Column: Default column
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
    View for task details, updates and deletion.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, board_id, task_id):
        """
        Retrieves task details.
        
        Args:
            request (Request): HTTP request
            board_id (int): ID of board
            task_id (int): ID of task
            
        Returns:
            Response: JSON with task details
            
        Raises:
            Http404: If task not found
        """
        task = self._get_task_if_authorized(board_id, task_id, request.user)
        if isinstance(task, Response):
            return task
        
        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, board_id, task_id):
        """
        Updates a task.
        
        Args:
            request (Request): HTTP request with update data
            board_id (int): ID of board
            task_id (int): ID of task to update
            
        Returns:
            Response: JSON with updated task or errors
            
        Raises:
            Http404: If task not found
        """
        task = self._get_task_if_authorized(board_id, task_id, request.user)
        if isinstance(task, Response):
            return task
        
        serializer = TaskSerializer(task, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not self._validate_assignee_reviewer(request.data, task.board):
            return Response(
                {'error': 'Assignee and reviewer must be board members'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task = serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, board_id, task_id):
        """
        Deletes a task.
        
        Args:
            request (Request): HTTP request
            board_id (int): ID of board
            task_id (int): ID of task to delete
            
        Returns:
            Response: Empty response on success, error otherwise
            
        Raises:
            Http404: If task not found
        """
        task = self._get_task_if_authorized(board_id, task_id, request.user)
        if isinstance(task, Response):
            return task
        
        if task.board.owner == request.user or task.created_by == request.user:
            task.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(
            {'error': 'Only the board owner or task creator can delete tasks'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    def _get_task_if_authorized(self, board_id, task_id, user):
        """
        Retrieves task if user is authorized.
        
        Args:
            board_id (int): Board ID
            task_id (int): Task ID
            user (User): User requesting access
            
        Returns:
            Task or Response: Task if authorized, error Response if not
            
        Raises:
            Http404: If task not found
        """
        task = get_object_or_404(Task, id=task_id, board_id=board_id)
        board = task.board
        
        if board.owner != user and not BoardMembership.objects.filter(
                board=board, user=user
            ).exists():
            return Response(
                {'error': 'No permission to access this task'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return task
    
    def _validate_assignee_reviewer(self, data, board):
        """
        Validates assignee and reviewer are board members.
        
        Args:
            data (dict): Request data
            board (Board): Board instance
            
        Returns:
            bool: True if valid
        """
        assignee_id = data.get('assignee_id')
        reviewer_id = data.get('reviewer_id')
        
        if assignee_id and not self._is_board_member(board, assignee_id):
            return False
        
        if reviewer_id and not self._is_board_member(board, reviewer_id):
            return False
        
        return True
    
    def _is_board_member(self, board, user_id):
        """
        Checks if user is board member.
        
        Args:
            board (Board): Board instance
            user_id (int): User ID to check
            
        Returns:
            bool: True if user is member
        """
        return (BoardMembership.objects.filter(
            board=board, user__id=user_id
        ).exists() or board.owner.id == user_id)