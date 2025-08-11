"""
API views for Kanban columns.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from kanban_app.models import Column, Board
from kanban_app.api.serializers.column_serializers import ColumnSerializer
from django.shortcuts import get_object_or_404
import logging



class ColumnListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating columns for a board.
    
    Handles GET requests to list columns and POST requests to create new ones.
    """
    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return columns for the specified board.
        
        Returns:
            QuerySet: Filtered Column queryset for the board
            
        Raises:
            NotFound: If board doesn't exist
        """
        board_id = self.kwargs.get('board_id')
        self._get_board(board_id) 
        return Column.objects.filter(board_id=board_id).order_by('position')
    
    def perform_create(self, serializer):
        """
        Create a new column for the specified board.
        
        Args:
            serializer (ColumnSerializer): Serializer with validated data
            
        Raises:
            NotFound: If board doesn't exist
            PermissionDenied: If user doesn't have access to the board
        """
        board_id = self.kwargs.get('board_id')
        board = self._get_board(board_id)
        
        self._check_board_access(board)
        position = self._get_next_position(board)
        
        serializer.save(board=board, position=position)
    
    def _get_board(self, board_id):
        """
        Get board by ID.
        
        Args:
            board_id (int): Board ID to find
            
        Returns:
            Board: Board object
            
        Raises:
            NotFound: If board doesn't exist
        """
        try:
            return Board.objects.get(id=board_id)
        except Board.DoesNotExist:
            raise NotFound(f"Board with id {board_id} not found")
    
    def _check_board_access(self, board):
        """
        Check if user has access to the board.
        
        Args:
            board (Board): Board to check
            
        Raises:
            PermissionDenied: If user doesn't have access
        """
        if not board.members.filter(id=self.request.user.id).exists():
            raise PermissionDenied("You do not have access to this board")
    
    def _get_next_position(self, board):
        """
        Get the next position value for a new column.
        
        Args:
            board (Board): Board object
            
        Returns:
            int: Next position value
        """
        last_column = Column.objects.filter(
            board=board
        ).order_by('-position').first()
        
        if last_column:
            return last_column.position + 1
        return 1


class ColumnDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating or deleting a column.
    
    Handles GET, PUT, PATCH and DELETE requests for individual columns.
    """
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Get column and check permissions.
        
        Returns:
            Column: The requested column object
            
        Raises:
            PermissionDenied: If user doesn't have access to the column's board
        """
        column = super().get_object()
        self._check_column_access(column)
        return column
    
    def _check_column_access(self, column):
        """
        Check user access to column's board.
        
        Args:
            column (Column): Column to check access for
            
        Raises:
            PermissionDenied: If user doesn't have access
        """
        if not column.board.members.filter(id=self.request.user.id).exists():
            raise PermissionDenied("You do not have access to this column")