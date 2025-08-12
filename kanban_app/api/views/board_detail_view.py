"""
View for board details and manipulation.

This module contains the BoardDetailView for retrieving, updating, and deleting
individual boards.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from kanban_app.models import Board, BoardMembership
from kanban_app.api.serializers.board_serializers import BoardUpdateSerializer
from kanban_app.api.views.utils_view import format_task_data, format_user_data
from django.shortcuts import get_object_or_404
import logging
import traceback
from django.http import Http404

logger = logging.getLogger(__name__)


class BoardDetailView(APIView):
    """
    View for retrieving, updating, and deleting a specific board.
    
    Requires authentication and either board ownership or membership.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk=None, board_id=None):
        """
        Retrieve a specific board with its tasks.
        
        Args:
            request (Request): The HTTP request.
            pk (int, optional): The board ID (primary key).
            board_id (int, optional): Alternative name for board ID.
            
        Returns:
            Response: The board data with tasks.
            
        Raises:
            Http404: If board not found.
            PermissionDenied: If user doesn't have access.
        """
        board_id = pk if pk is not None else board_id
        
        try:
            board = self._get_board_if_authorized(board_id, request.user)
            board_data = self._prepare_board_data(board)
            return Response(board_data)
            
        except Exception as e:
            self._handle_exception(e)
            return Response(
                {"detail": "An error occurred while retrieving the board"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, pk=None, board_id=None):
        """
        Update a board's title and/or members.
        
        Args:
            request (Request): The HTTP request.
            pk (int, optional): The board ID (primary key).
            board_id (int, optional): Alternative name for board ID.
            
        Returns:
            Response: The updated board data.
            
        Raises:
            Http404: If board not found.
            PermissionDenied: If user doesn't have access.
        """
        board_id = pk if pk is not None else board_id
        board = self._get_board_if_authorized(board_id, request.user)
        
        serializer = BoardUpdateSerializer(
            board, 
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            updated_board = serializer.save()
            response_data = self._format_update_response(updated_board)
            return Response(response_data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk=None, board_id=None):
        """
        Delete a board (owner only).
        
        Args:
            request (Request): The HTTP request.
            pk (int, optional): The board ID (primary key).
            board_id (int, optional): Alternative name for board ID.
            
        Returns:
            Response: 204 No Content on success.
            
        Raises:
            Http404: If board not found.
            PermissionDenied: If user is not the board owner.
        """
        board_id = pk if pk is not None else board_id
        board = self._get_board_if_authorized(board_id, request.user)
        
        if board.owner != request.user:
            return Response(
                {"detail": "Only the board owner can delete the board"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def _handle_exception(self, exception):
        """
        Log exception details and re-raise Http404 and PermissionDenied.
        
        Args:
            exception (Exception): The exception to handle.
            
        Raises:
            Http404: If the original exception was Http404.
            PermissionDenied: If the original exception was PermissionDenied.
        """
        logger.error(f"Board retrieval error: {str(exception)}")
        logger.error(f"Error type: {type(exception).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        if isinstance(exception, Http404):
            raise exception
        if isinstance(exception, PermissionDenied):
            raise exception
    
    def _get_board_if_authorized(self, board_id, user):
        """
        Retrieve board by ID and check user permissions.
        
        Args:
            board_id (int): The board ID.
            user (User): The requesting user.
            
        Returns:
            Board: The requested board.
            
        Raises:
            Http404: If board doesn't exist.
            PermissionDenied: If user doesn't have access.
        """
        board = get_object_or_404(Board, pk=board_id)
        
        is_owner = board.owner == user
        is_member = BoardMembership.objects.filter(
            board=board,
            user=user
        ).exists()
        
        if not (is_owner or is_member):
            raise PermissionDenied("You must be a member or owner of this board")
            
        return board
    
    def _prepare_board_data(self, board):
        """
        Prepare board data for response.
        
        Args:
            board (Board): The board object.
            
        Returns:
            dict: Formatted board data including tasks.
        """
        members_data = []
        memberships = BoardMembership.objects.filter(board=board)
        for membership in memberships:
            members_data.append(format_user_data(membership.user))
        
        tasks_data = []
        for column in board.columns.all():
            for task in column.tasks.all():
                tasks_data.append(format_task_data(task))
        
        board_data = {
            "id": board.id,
            "title": getattr(board, 'title', getattr(board, 'name', '')),
            "owner_id": board.owner.id,
            "members": members_data,
            "tasks": tasks_data
        }
        
        return board_data
    
    def _format_update_response(self, board):
        """
        Format the response data for board updates.
        
        Args:
            board (Board): The updated board object.
            
        Returns:
            dict: Formatted response data with owner and members information.
        """
        owner_data = format_user_data(board.owner)
        
        members_data = []
        memberships = BoardMembership.objects.filter(board=board)
        for membership in memberships:
            members_data.append(format_user_data(membership.user))
        
        return {
            "id": board.id,
            "title": getattr(board, 'title', getattr(board, 'name', '')),
            "owner_data": owner_data,
            "members_data": members_data
        }