"""
API views for Kanban columns.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from kanban_app.models import Column, Board
from kanban_app.api.serializers.column_serializers import ColumnSerializer
from django.shortcuts import get_object_or_404


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
        """
        board_id = self.kwargs['board_id']
        return Column.objects.filter(board_id=board_id).order_by('position')
    
    def perform_create(self, serializer):
        """
        Create a new column for the specified board.
        
        Args:
            serializer (ColumnSerializer): Serializer with validated data
            
        Raises:
            PermissionDenied: If user doesn't have access to the board
        """
        board_id = self.kwargs['board_id']
        board = get_object_or_404(Board, pk=board_id)
        
        self._check_board_access(board)
        position = self._get_next_position(board)
        serializer.save(board=board, position=position)
    
    def _check_board_access(self, board):
        """
        Check if user has access to the board.
        
        Args:
            board (Board): Board to check
            
        Raises:
            PermissionDenied: If user doesn't have access
        """
        if not board.members.filter(id=self.request.user.id).exists():
            return Response(
                {"error": "You do not have access to this board"}, 
                status=status.HTTP_403_FORBIDDEN
            )
    
    def _get_next_position(self, board):
        """
        Get the next position value for a new column.
        
        Args:
            board (Board): Board object
            
        Returns:
            int: Next position value
        """
        last_position = Column.objects.filter(
            board=board
        ).order_by('-position').first()
        
        if last_position:
            return last_position.position + 1
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
        
        if not column.board.members.filter(id=self.request.user.id).exists():
            return Response(
                {"error": "You do not have access to this column"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        return column