"""
API views for Kanban boards.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from kanban_app.models import Board, BoardMembership
from kanban_app.api.serializers.board_serializers import BoardSerializer, BoardDetailSerializer
import logging

logger = logging.getLogger(__name__)


class BoardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Kanban boards.
    
    Provides endpoints for creating, retrieving, updating and deleting boards.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on action.
        
        Returns:
            Serializer: BoardDetailSerializer for retrieve, BoardSerializer otherwise
        """
        if self.action == 'retrieve':
            return BoardDetailSerializer
        return BoardSerializer
    
    def get_queryset(self):
        """
        Return boards accessible to current user.
        
        Returns:
            QuerySet: Filtered Board queryset for the current user
        """
        user = self.request.user
        return Board.objects.filter(members=user)
    
    def create(self, request, *args, **kwargs):
        """
        Create a new board.
        
        Args:
            request (Request): HTTP request with board data
            
        Returns:
            Response: Created board data or error
            
        Raises:
            ValidationError: If board data is invalid
        """
        data = request.data.copy()
        self._convert_title_to_name(data)
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        board = serializer.save(owner=request.user)
        
        self._add_creator_as_admin(board, request.user)
        
        logger.info("Board created successfully")
        return Response(
            BoardDetailSerializer(board).data, 
            status=status.HTTP_201_CREATED
        )
    
    def _convert_title_to_name(self, data):
        """
        Convert title field to name field for backward compatibility.
        
        Args:
            data (dict): Request data dictionary
        """
        if 'title' in data and 'name' not in data:
            data['name'] = data['title']
    
    def _add_creator_as_admin(self, board, user):
        """
        Add the creator as admin member to the board.
        
        Args:
            board (Board): Board object
            user (User): User who created the board
        """
        BoardMembership.objects.create(
            board=board,
            user=user,
            role='ADMIN'
        )