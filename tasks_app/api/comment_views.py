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
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]
    
    def get_board_and_task(self, board_id, task_id):
        """
        Retrieve the board and task based on the provided IDs.
        
        Args:
            board_id (int): The ID of the board.
            task_id (int): The ID of the task.
            
        Returns:
            tuple: A tuple containing (board, task).
            
        Raises:
            Http404: If the board or task doesn't exist or if the task doesn't belong to the board.
        """
        board = get_object_or_404(Board, pk=board_id)
        columns = board.columns.values_list('id', flat=True)
        task = get_object_or_404(Task, pk=task_id, column__in=columns)
        return board, task
    
    def get(self, request, board_id, task_id):
        """
        Retrieve all comments for a specific task.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            task_id (int): The ID of the task.
            
        Returns:
            Response: A response containing a list of comments.
        """
        board, task = self.get_board_and_task(board_id, task_id)
        self.check_object_permissions(request, board)
        
        comments = self._get_comments_for_task(task)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    def _get_comments_for_task(self, task):
        """
        Get comments for a task ordered by creation time.
        
        Args:
            task (Task): The task to get comments for.
            
        Returns:
            QuerySet: The comments for the task.
        """
        return Comment.objects.filter(task=task).order_by('created_at')
    
    def post(self, request, board_id, task_id):
        """
        Create a new comment for a specific task.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            task_id (int): The ID of the task.
            
        Returns:
            Response: A response containing the created comment data.
            
        Raises:
            ValidationError: If the request data is invalid.
        """
        board, task = self.get_board_and_task(board_id, task_id)
        self.check_object_permissions(request, board)
        
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentDetailView(APIView):
    """
    Delete a specific comment.
    
    Only the author of the comment can delete it.
    """
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]
    
    def get_objects(self, board_id, task_id, pk):
        """
        Retrieve the board, task and comment based on the provided IDs.
        
        Args:
            board_id (int): The ID of the board.
            task_id (int): The ID of the task.
            pk (int): The ID of the comment.
            
        Returns:
            tuple: A tuple containing (board, task, comment).
            
        Raises:
            Http404: If any object doesn't exist or if relationships are incorrect.
        """
        board = get_object_or_404(Board, pk=board_id)
        columns = board.columns.values_list('id', flat=True)
        task = get_object_or_404(Task, pk=task_id, column__in=columns)
        comment = get_object_or_404(Comment, pk=pk, task=task)
        return board, task, comment
    
    def delete(self, request, board_id, task_id, pk):
        """
        Delete a specific comment.
        
        Args:
            request (Request): The HTTP request object.
            board_id (int): The ID of the board.
            task_id (int): The ID of the task.
            pk (int): The ID of the comment.
            
        Returns:
            Response: An empty response with 204 status code.
            
        Raises:
            PermissionDenied: If the user is not the author of the comment.
        """
        board, task, comment = self.get_objects(board_id, task_id, pk)
        self.check_object_permissions(request, board)
        
        if comment.author != request.user:
            return Response(
                {"detail": "You can only delete your own comments"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)