from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from kanban_app.models import Board, Column
from kanban_app.api.serializers.column_serializers import ColumnSerializer
from kanban_app.api.permissions import IsOwnerOrMember


class ColumnListCreateView(generics.ListCreateAPIView):
    """
    List columns for a board or create a new column.
    
    Provides endpoints to retrieve all columns for a specific board
    and create new columns within that board.
    """
    serializer_class = ColumnSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        """
        Get columns for the current board ordered by position.
        
        Returns:
            QuerySet: Filtered columns for the specified board
        """
        board_id = self.kwargs.get("board_id")
        return Column.objects.filter(board_id=board_id).order_by('position')

    def perform_create(self, serializer):
        """
        Create a new column for the specified board.
        
        Args:
            serializer (ColumnSerializer): Validated column data
            
        Raises:
            NotFound: If board doesn't exist
            PermissionDenied: If user lacks permission to add columns
        """
        board_id = self.kwargs.get("board_id")
        board = self._get_board_or_raise(board_id)
        self._check_board_permissions(board)
        serializer.save(board=board)

    def _get_board_or_raise(self, board_id):
        """
        Retrieve board by ID or raise NotFound exception.
        
        Args:
            board_id (int): Board primary key
            
        Returns:
            Board: The requested board instance
            
        Raises:
            NotFound: If board with given ID doesn't exist
        """
        try:
            return Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            raise NotFound("Board not found")

    def _check_board_permissions(self, board):
        """
        Verify user has permission to modify the board.
        
        Args:
            board (Board): Board instance to check permissions for
            
        Raises:
            PermissionDenied: If user lacks permission to add columns
        """
        permission_check = IsOwnerOrMember()
        has_permission = permission_check.has_object_permission(
            self.request, self, board
        )
        if not has_permission:
            raise PermissionDenied(
                "You don't have permission to add columns to this board"
            )


class ColumnDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific column.
    
    Provides endpoints for individual column operations including
    viewing, updating, and deleting columns.
    """
    serializer_class = ColumnSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get all columns queryset.
        
        Returns:
            QuerySet: All column objects
        """
        return Column.objects.all()

    def get_object(self):
        """
        Get column object with permission check.
        
        Returns:
            Column: The requested column instance
            
        Raises:
            PermissionDenied: If user lacks access to the column
        """
        obj = super().get_object()
        self._check_column_permissions(obj)
        return obj

    def _check_column_permissions(self, column):
        """
        Verify user has permission to access the column.
        
        Args:
            column (Column): Column instance to check permissions for
            
        Raises:
            PermissionDenied: If user lacks permission to access column
        """
        board = column.board
        is_owner = board.owner == self.request.user
        is_member = self.request.user in board.members.all()
        
        if not (is_owner or is_member):
            raise PermissionDenied(
                "You don't have permission to access this column"
            )