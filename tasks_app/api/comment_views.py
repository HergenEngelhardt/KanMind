"""Views for managing task comments.

This module contains all views related to comment creation, retrieval,
and deletion on tasks.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from tasks_app.models import Task, Comment
from kanban_app.models import BoardMembership
from .serializers import CommentSerializer
from django.shortcuts import get_object_or_404

class CommentListCreateView(APIView):
    """
    View for listing and creating comments on tasks.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, board_id, task_id):
        """
        Lists all comments for a task.
        
        Args:
            request (Request): HTTP request
            board_id (int): ID of board
            task_id (int): ID of task
            
        Returns:
            Response: List of comments
            
        Raises:
            Http404: If task not found
        """
        task = self._get_task_if_authorized(board_id, task_id, request.user)
        if isinstance(task, Response):
            return task
            
        comments = Comment.objects.filter(task=task)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, board_id, task_id):
        """
        Creates a new comment on a task.
        
        Args:
            request (Request): HTTP request with comment data
            board_id (int): ID of board
            task_id (int): ID of task
            
        Returns:
            Response: Created comment data
            
        Raises:
            Http404: If task not found
        """
        task = self._get_task_if_authorized(board_id, task_id, request.user)
        if isinstance(task, Response):
            return task
            
        serializer = CommentSerializer(data=request.data)
        
        if serializer.is_valid():
            comment = serializer.save(task=task, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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


class CommentDeleteView(APIView):
    """
    View for deleting comments.
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, board_id, task_id, comment_id):
        """
        Deletes a comment if user is the author.
        
        Args:
            request (Request): HTTP request
            board_id (int): ID of board
            task_id (int): ID of task
            comment_id (int): ID of comment to delete
            
        Returns:
            Response: Empty success response or error
            
        Raises:
            Http404: If comment not found
        """
        task = self._get_task_if_authorized(board_id, task_id, request.user)
        if isinstance(task, Response):
            return task
            
        comment = get_object_or_404(Comment, id=comment_id, task=task)
        
        if comment.author != request.user:
            return Response(
                {'error': 'You can only delete your own comments'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
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