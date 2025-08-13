"""
API views for task comments.

This module contains views for listing, creating, and deleting comments.
"""
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from kanban_app.models import Board
from tasks_app.models import Task, Comment
from .serializers import CommentSerializer
from .permissions import IsBoardMember


class CommentListCreateView(APIView):
    """
    List and create comments for a specific task.
    
    Requires the user to be a member of the board that the task belongs to.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, task_id):
        """
        List all comments for a specific task.
        
        Args:
            request (Request): The HTTP request
            task_id (int): The task ID
            
        Returns:
            Response: List of comments for the task
            
        Raises:
            Http404: If task not found
            PermissionDenied: If user doesn't have access
        """
        task = self._get_task_or_404(task_id)
        self._check_board_membership(request, task.column.board)
        
        comments = self._get_comments_for_task(task)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, task_id):
        """
        Create a new comment for a task.
        
        Args:
            request (Request): The HTTP request with comment data
            task_id (int): The task ID
            
        Returns:
            Response: Created comment data or error
            
        Raises:
            Http404: If task not found
            PermissionDenied: If user doesn't have access
        """
        task = self._get_task_or_404(task_id)
        self._check_board_membership(request, task.column.board)
        
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
            raise PermissionDenied("You must be a member of this board to access its tasks")
    
    def _get_comments_for_task(self, task):
        """
        Get all comments for a task.
        
        Args:
            task (Task): The task to get comments for
            
        Returns:
            QuerySet: Comments for the task
        """
        return Comment.objects.filter(task=task).order_by('created_at')


class CommentDetailView(APIView):
    """
    Delete a specific comment.
    
    Only the author of the comment can delete it.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, task_id, pk):
        """
        Delete a specific comment.
        
        Args:
            request (Request): The HTTP request
            task_id (int): The task ID
            pk (int): The comment ID
            
        Returns:
            Response: Empty response on success
            
        Raises:
            Http404: If task or comment not found
            PermissionDenied: If user doesn't have delete permission
        """
        task = self._get_task_or_404(task_id)
        self._check_board_membership(request, task.column.board)
        
        comment = self._get_comment_or_404(task, pk)
        
        if comment.created_by != request.user:
            raise PermissionDenied("Only the author can delete this comment")
        
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
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
    
    def _get_comment_or_404(self, task, comment_id):
        """
        Get comment by ID and task or raise 404.
        
        Args:
            task (Task): The task instance
            comment_id (int): The comment ID
            
        Returns:
            Comment: The comment instance
            
        Raises:
            Http404: If comment not found
        """
        return get_object_or_404(Comment, id=comment_id, task=task)
    
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
            raise PermissionDenied("You must be a member of this board to access its tasks")


class BoardCommentListCreateView(APIView):
    """
    List and create comments for a specific task within a board context.
    
    Requires the user to be a member of the board that the task belongs to.
    """
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]
    
    def get(self, request, board_id, task_id):
        """
        List all comments for a task within a board.
        
        Args:
            request (Request): The HTTP request
            board_id (int): The board ID
            task_id (int): The task ID
            
        Returns:
            Response: List of comments for the task
            
        Raises:
            Http404: If task or board not found
        """
        board, task = self._get_board_and_task(board_id, task_id)
        self.check_object_permissions(request, board)
        
        comments = Comment.objects.filter(task=task).order_by('created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    def post(self, request, board_id, task_id):
        """
        Create a new comment for a task within a board.
        
        Args:
            request (Request): The HTTP request with comment data
            board_id (int): The board ID
            task_id (int): The task ID
            
        Returns:
            Response: Created comment data or error
            
        Raises:
            Http404: If task or board not found
        """
        board, task = self._get_board_and_task(board_id, task_id)
        self.check_object_permissions(request, board)
        
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_board_and_task(self, board_id, task_id):
        """
        Get board and task by their IDs or raise 404.
        
        Args:
            board_id (int): The board ID
            task_id (int): The task ID
            
        Returns:
            tuple: (Board, Task) instances
            
        Raises:
            Http404: If board or task not found
        """
        board = get_object_or_404(Board, id=board_id)
        task = get_object_or_404(Task, id=task_id, column__board=board)
        return board, task


class BoardCommentDetailView(APIView):
    """
    Delete a specific comment within a board context.
    
    Only the author of the comment can delete it.
    """
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]
    
    def delete(self, request, board_id, task_id, pk):
        """
        Delete a specific comment within a board.
        
        Args:
            request (Request): The HTTP request
            board_id (int): The board ID
            task_id (int): The task ID
            pk (int): The comment ID
            
        Returns:
            Response: Empty response on success
            
        Raises:
            Http404: If board, task, or comment not found
            PermissionDenied: If user doesn't have delete permission
        """
        board = get_object_or_404(Board, id=board_id)
        self.check_object_permissions(request, board)
        
        task = get_object_or_404(Task, id=task_id, column__board=board)
        comment = get_object_or_404(Comment, id=pk, task=task)
        
        if comment.created_by != request.user:
            raise PermissionDenied("Only the author can delete this comment")
        
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)