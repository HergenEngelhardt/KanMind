"""
View for board details and manipulation.

This module contains the BoardDetailView for retrieving, updating, and deleting
individual boards.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from kanban_app.models import Board, BoardMembership
from kanban_app.api.serializers.board_serializers import BoardUpdateSerializer
from kanban_app.api.views.utils_view import format_task_data, format_user_data  # Korrigierter Import
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

class BoardDetailView(APIView):
    """
    View for retrieving, updating, and deleting boards.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, board_id):
        """
        Retrieves board details with tasks.
        
        Args:
            request (Request): HTTP request
            board_id (int): ID of board to retrieve
            
        Returns:
            Response: JSON with board details
            
        Raises:
            Http404: If board not found
        """
        try:
            board = self._get_board_if_authorized(board_id, request.user)
            if isinstance(board, Response):
                return board
                
            members = self._get_board_members(board)
            tasks = self._get_board_tasks(board)
            
            response_data = self._prepare_response_data(board, members, tasks)
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Board.DoesNotExist:
            return self._create_board_not_found_response()
        except Exception as e:
            return self._create_server_error_response(e)
    
    def patch(self, request, board_id):
        """
        Updates board title and members.
        
        Args:
            request (Request): HTTP request with update data
            board_id (int): ID of board to update
            
        Returns:
            Response: JSON with updated board data
            
        Raises:
            Http404: If board not found
        """
        try:
            board = get_object_or_404(Board, id=board_id)
            
            if not self._user_has_board_access(board, request.user):
                return Response(
                    {'error': 'No permission to update this board'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = BoardUpdateSerializer(
                board, 
                data=request.data, 
                partial=True
            )
            
            if serializer.is_valid():
                board = serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    serializer.errors, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Board.DoesNotExist:
            return Response(
                {'error': 'Board not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': 'Server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, board_id):
        """
        Deletes a board if user is owner.
        
        Args:
            request (Request): HTTP request
            board_id (int): ID of board to delete
            
        Returns:
            Response: Empty response on success
            
        Raises:
            Http404: If board not found
        """
        try:
            board = get_object_or_404(Board, id=board_id)
            
            if board.owner != request.user:
                return Response(
                    {'error': 'Only the owner can delete this board'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            board.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Board.DoesNotExist:
            return Response(
                {'error': 'Board not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': 'Server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_board_if_authorized(self, board_id, user):
        """
        Retrieves board if user has access.
        
        Args:
            board_id (int): Board ID
            user (User): User requesting access
            
        Returns:
            Board or Response: Board if access granted, error Response if denied
            
        Raises:
            Http404: If board not found
        """
        board = get_object_or_404(Board, id=board_id)
        
        if not self._user_has_board_access(board, user):
            return Response(
                {'error': 'No permission to access this board'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return board
    
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
    
    def _get_board_members(self, board):
        """
        Gets board members formatted for response.
        
        Args:
            board (Board): Board instance
            
        Returns:
            list: List of member data dictionaries
        """
        members = []
        for membership in BoardMembership.objects.filter(board=board):
            user = membership.user
            members.append(format_user_data(user))
        return members
    
    def _get_board_tasks(self, board):
        """
        Gets board tasks formatted for response.
        
        Args:
            board (Board): Board instance
            
        Returns:
            list: List of task data dictionaries
        """
        tasks = []
        for column in board.columns.all():
            for task in column.tasks.all():
                task_data = format_task_data(task)
                tasks.append(task_data)
        return tasks
    
    def _prepare_response_data(self, board, members, tasks):
        """
        Prepares full board response data.
        
        Args:
            board (Board): Board instance
            members (list): List of formatted member data
            tasks (list): List of formatted task data
            
        Returns:
            dict: Response data
        """
        return {
            'id': board.id,
            'title': board.name,
            'owner_id': board.owner.id,
            'members': members,
            'tasks': tasks
        }
    
    def _create_board_not_found_response(self):
        """
        Creates a board not found error response.
        
        Returns:
            Response: Error response
        """
        logger.error("Board retrieval error: No Board matches the given query.")
        return Response(
            {'error': 'Board not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    def _create_server_error_response(self, exception):
        """
        Creates a server error response.
        
        Args:
            exception (Exception): Exception that occurred
            
        Returns:
            Response: Error response
        """
        logger.error(f"Board retrieval error: {str(exception)}")
        return Response(
            {'error': 'Server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )