from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from kanban_app.models import Board, Column
from kanban_app.api.serializers.column_serializers import ColumnSerializer
from kanban_app.api.permissions import IsOwnerOrMember


class ColumnListCreateView(generics.ListCreateAPIView):
    """List columns for a board or create a new column."""
    serializer_class = ColumnSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        board_id = self.kwargs.get("board_id")
        return Column.objects.filter(board_id=board_id).order_by('position')

    def perform_create(self, serializer):
        board_id = self.kwargs.get("board_id")
        board = self._get_board_or_raise(board_id)
        self._check_board_permissions(board)
        serializer.save(board=board)

    def _get_board_or_raise(self, board_id):
        try:
            return Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            raise NotFound("Board not found")

    def _check_board_permissions(self, board):
        if not IsOwnerOrMember().has_object_permission(self.request, self, board):
            raise PermissionDenied(
                "You don't have permission to add columns to this board"
            )


class ColumnDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a specific column."""
    serializer_class = ColumnSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Column.objects.all()

    def get_object(self):
        obj = super().get_object()
        self._check_column_permissions(obj)
        return obj

    def _check_column_permissions(self, column):
        board = column.board
        if not (board.owner == self.request.user or self.request.user in board.members.all()):
            raise PermissionDenied(
                "You don't have permission to access this column"
            )