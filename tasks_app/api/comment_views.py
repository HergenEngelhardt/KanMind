"""
API views for task comments.

This module contains views for listing, creating, and deleting comments.
"""
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
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
        Retrieve all comments for a specific task.
        
        Args:
            request (Request): The HTTP request object.
            task_id (int): The ID of the task.
            
        Returns:
            Response: A response containing a list of comments.
        """
        task = self._get_task_or_404(task_id)
        board = task.column.board
        self._check_board_membership(request, board)
        
        comments = self._get_comments_for_task(task)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    def post(self, request, task_id):
        """
        Create a new comment for a specific task.
        
        Args:
            request (Request): The HTTP request object.
            task_id (int): The ID of the task.
            
        Returns:
            Response: A response containing the created comment data.
            
        Raises:
            ValidationError: If the request data is invalid.
        """
        task = self._get_task_or_404(task_id)
        board = task.column.board
        self._check_board_membership(request, board)
        
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
    
    def _get_comments_for_task(self, task):
        """
        Get comments for a task ordered by creation time.
        
        Args:
            task (Task): The task to get comments for.
            
        Returns:
            QuerySet: The comments for the task.
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
            request (Request): The HTTP request object.
            task_id (int): The ID of the task.
            pk (int): The ID of the comment.
            
        Returns:
            Response: An empty response with 204 status code.
            
        Raises:
            PermissionDenied: If the user is not the author of the comment.
        """
        task = self._get_task_or_404(task_id)
        board = task.column.board
        self._check_board_membership(request, board)
        
        comment = self._get_comment_or_404(task, pk)
        
        if comment.author != request.user:
            return Response(
                {"detail": "You can only delete your own comments"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        comment.delete()
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
    
    def _get_comment_or_404(self, task, comment_id):
        """
        Get a comment for a specific task by ID or return 404.
        
        Args:
            task (Task): The task object.
            comment_id (int): The comment ID.
            
        Returns:
            Comment: The comment object.
            
        Raises:
            Http404: If the comment doesn't exist or doesn't belong to the task.
        """
        return get_object_or_404(Comment, pk=comment_id, task=task)
    
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