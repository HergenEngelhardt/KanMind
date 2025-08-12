"""
Views for listing and creating boards.

This module contains the BoardListCreateView for retrieving all boards
a user has access to and for creating new boards.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from kanban_app.models import Board, BoardMembership
from kanban_app.api.serializers.board_serializers import BoardListSerializer
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class BoardListCreateView(APIView):
    """
    View for listing and creating boards.
    
    Handles GET requests to list user's boards and POST requests to create new boards.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Lists all boards where user is member or owner.
        
        Args:
            request (Request): HTTP request
            
        Returns:
            Response: JSON list of boards
        """
        user_boards = self._get_user_boards(request.user)
        serializer = BoardListSerializer(user_boards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """
        Creates new board with the user as admin.
        
        Args:
            request (Request): HTTP request with board data
            
        Returns:
            Response: JSON with created board data
            
        Raises:
            ValidationError: If title is missing
        """
        title = request.data.get('title')
        member_ids = request.data.get('members', [])
        
        if not title:
            return self._title_required_error()
        
        board = self._create_board(request.user, title)
        self._add_members(board, member_ids, request.user.id)
        
        response_data = self._prepare_response_data(board, request.user.id)
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    def _get_user_boards(self, user):
        """
        Get boards where user is member or owner.
        
        Args:
            user (User): User to get boards for
            
        Returns:
            QuerySet: User's boards
        """
        return Board.objects.filter(boardmembership__user=user).distinct()
    
    def _title_required_error(self):
        """
        Create response for missing title error.
        
        Returns:
            Response: Error response
        """
        return Response(
            {'error': 'Title is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def _create_board(self, user, title):
        """
        Creates a new board.
        
        Args:
            user (User): User creating the board
            title (str): Board title
            
        Returns:
            Board: New board instance
        """
        logger.info(f"Board creation request from user: {user}")
        board = Board.objects.create(name=title, owner=user)
        
        BoardMembership.objects.create(
            board=board, user=user, role='ADMIN'
        )
        
        return board
    
    def _add_members(self, board, member_ids, owner_id):
        """
        Adds members to board.
        
        Args:
            board (Board): Board instance
            member_ids (list): List of user IDs to add
            owner_id (int): ID of board owner
        """
        for member_id in member_ids:
            if member_id != owner_id:
                try:
                    user = User.objects.get(id=member_id)
                    BoardMembership.objects.create(
                        board=board, user=user, role='MEMBER'
                    )
                except User.DoesNotExist:
                    pass
    
    def _prepare_response_data(self, board, owner_id):
        """
        Prepares response data for board creation.
        
        Args:
            board (Board): Board instance
            owner_id (int): ID of board owner
            
        Returns:
            dict: Response data
        """
        return {
            'id': board.id,
            'title': board.name,
            'member_count': board.members.count(),
            'ticket_count': 0,
            'tasks_to_do_count': 0,
            'tasks_high_prio_count': 0,
            'owner_id': owner_id
        }