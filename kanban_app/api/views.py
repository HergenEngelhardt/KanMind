import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.contrib.auth.models import User
from kanban_app.models import Board, Column
from tasks_app.models import Task
from kanban_app.api.serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
    UserSerializer,
    ColumnSerializer,
)
from kanban_app.api.permissions import IsOwnerOrMember, IsOwner

logger = logging.getLogger(__name__)

class BoardListCreateView(ListCreateAPIView):
    """
    List user's boards or create a new board.
    
    GET: Returns boards where user is owner or member
    POST: Creates new board with authenticated user as owner
    """
    serializer_class = BoardListSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        """Get boards where user is owner or member."""
        user = self.request.user
        return Board.objects.filter(
            models.Q(owner_id=user) | models.Q(members=user)
        ).distinct()

    def get_permissions(self):
        """Set permissions based on request method."""
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [IsOwnerOrMember()]

    def perform_create(self, serializer):
        """Create board and add owner as member."""
        board = serializer.save(owner=self.request.user)
        self._add_owner_as_member(board)

    def _add_owner_as_member(self, board):
        """Add board owner as member if not already added."""
        if not board.members.filter(id=self.request.user.id).exists():
            board.members.add(self.request.user)


class BoardDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific board.
    
    GET: Get board details with members and columns
    PATCH: Update board name or description
    DELETE: Delete board (owner only)
    """
    serializer_class = BoardDetailSerializer
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        """Set permissions based on request method."""
        if self.request.method == "DELETE":
            return [IsOwner()]
        return [IsOwnerOrMember()]

    def get_queryset(self):
        """Return all boards for permission checking."""
        return Board.objects.all()

    def partial_update(self, request, *args, **kwargs):
        """Update board with field restrictions."""
        if not self._validate_update_fields(request.data):
            return self._field_restriction_error()
        
        try:
            response = super().partial_update(request, *args, **kwargs)
            if response.status_code == status.HTTP_200_OK:
                response.data = self._format_update_response(response.data)
            return response
        except Exception as e:
            logger.error(f"Board update error: {str(e)}")
            return self._server_error_response()

    def delete(self, request, *args, **kwargs):
        """Delete board and return success message."""
        super().delete(request, *args, **kwargs)
        return Response(
            {"message": "Board successfully deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )

    def _validate_update_fields(self, data):
        """Validate only allowed fields are being updated."""
        allowed_fields = {"name", "description"}
        return all(field in allowed_fields for field in data.keys())

    def _field_restriction_error(self):
        """Return error for invalid field updates."""
        return Response(
            {"error": "Only the fields 'name' and 'description' can be edited."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _format_update_response(self, response_data):
        """Format update response with owner data."""
        formatted_data = response_data.copy()
        if "owner_id" in formatted_data:
            del formatted_data["owner_id"]
        
        formatted_data["owner_data"] = UserSerializer(
            self.get_object().owner
        ).data
        return formatted_data

    def _server_error_response(self):
        """Return generic server error response."""
        return Response(
            {"error": "A server error has occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class EmailCheckView(APIView):
    """
    Check if user exists by email address.
    
    Used for adding members to boards by email lookup.
    Returns user information if found.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Check if user with email exists."""
        email = request.query_params.get("email")
        
        if not email:
            return self._email_required_error()
        
        user = self._get_user_by_email(email)
        if user:
            return self._user_found_response(user)
        
        return self._user_not_found_response()

    def _get_user_by_email(self, email):
        """Get user by email address."""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def _email_required_error(self):
        """Return error for missing email parameter."""
        return Response(
            {"error": "Email parameter is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    def _user_found_response(self, user):
        """Return user information response."""
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "fullname": f"{user.first_name} {user.last_name}".strip() or user.email,
                "exists": True 
            },
            status=status.HTTP_200_OK,
        )

    def _user_not_found_response(self):
        """Return user not found response."""
        return Response(
            {"exists": False}, 
            status=status.HTTP_200_OK 
        )

class ColumnListCreateView(generics.ListCreateAPIView):
    """
    List columns for a board or create a new column.
    
    GET: Returns columns for specified board
    POST: Creates new column in specified board
    """
    
    serializer_class = ColumnSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        """Get columns for specified board."""
        board_id = self.kwargs.get("board_id")
        return Column.objects.filter(board_id=board_id).order_by('position')

    def perform_create(self, serializer):
        """Create column with board permission check."""
        board_id = self.kwargs.get("board_id")
        board = self._get_board_or_raise(board_id)
        self._check_board_permissions(board)
        serializer.save(board=board)

    def _get_board_or_raise(self, board_id):
        """Get board or raise NotFound exception."""
        try:
            return Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            raise NotFound("Board not found")

    def _check_board_permissions(self, board):
        """Check if user has permission to modify board."""
        if not IsOwnerOrMember().has_object_permission(self.request, self, board):
            raise PermissionDenied(
                "You don't have permission to add columns to this board"
            )

class ColumnDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific column.
    
    Requires board membership permissions.
    """
    
    serializer_class = ColumnSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        """Return all columns for permission checking."""
        return Column.objects.all()

    def get_object(self):
        """Get column with permission check."""
        obj = super().get_object()
        self._check_column_permissions(obj)
        return obj

    def _check_column_permissions(self, column):
        """Check if user has permission to access column."""
        board = column.board
        if not (board.owner == self.request.user or self.request.user in board.members.all()):
            raise PermissionDenied(
                "You don't have permission to access this column"
            )

class TaskReorderView(APIView):
    """
    Reorder tasks within and between columns.
    
    Handles task position updates and maintains correct ordering.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Reorder task position."""
        task_data = self._extract_task_data(request.data)
        
        try:
            task, column = self._get_task_and_column(task_data)
            self._check_task_permissions(task, request.user)
            self._reorder_task(task, column, task_data['position'])
            
            return Response({"success": True}, status=status.HTTP_200_OK)
        except (Task.DoesNotExist, Column.DoesNotExist):
            return self._not_found_error()
        except PermissionDenied as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Task reorder error: {str(e)}")
            return Response(
                {"error": "Internal server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _extract_task_data(self, data):
        """Extract task reorder data from request."""
        return {
            'task_id': data.get("task_id"),
            'column_id': data.get("column_id"),
            'position': data.get("position", 0)
        }

    def _get_task_and_column(self, task_data):
        """Get task and column instances."""
        task = Task.objects.get(id=task_data['task_id'])
        column = Column.objects.get(id=task_data['column_id'])
        return task, column

    def _check_task_permissions(self, task, user):
        """Check if user can modify task."""
        board = task.column.board
        if not (board.owner == user or user in board.members.all()):
            raise PermissionDenied(
                "You don't have permission to modify this task"
            )

    def _reorder_task(self, task, new_column, new_position):
        """Reorder task and update positions."""
        old_column = task.column
        old_position = task.position

        task.column = new_column
        task.position = new_position
        task.save()

        if old_column == new_column:
            self._reorder_within_column(old_column, old_position, new_position, task.id)
        else:
            self._reorder_between_columns(old_column, new_column, old_position, new_position, task.id)

    def _reorder_within_column(self, column, old_pos, new_pos, task_id):
        """Reorder tasks within same column."""
        if old_pos < new_pos:
            Task.objects.filter(
                column=column, 
                position__gt=old_pos, 
                position__lte=new_pos
            ).exclude(id=task_id).update(position=models.F("position") - 1)
        elif old_pos > new_pos:
            Task.objects.filter(
                column=column, 
                position__gte=new_pos, 
                position__lt=old_pos
            ).exclude(id=task_id).update(position=models.F("position") + 1)

    def _reorder_between_columns(self, old_column, new_column, old_pos, new_pos, task_id):
        """Reorder tasks between different columns."""
        Task.objects.filter(
            column=old_column, 
            position__gt=old_pos
        ).update(position=models.F("position") - 1)

        Task.objects.filter(
            column=new_column, 
            position__gte=new_pos
        ).exclude(id=task_id).update(position=models.F("position") + 1)

    def _not_found_error(self):
        """Return task or column not found error."""
        return Response(
            {"error": "Task or column not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

from rest_framework import viewsets
from rest_framework.decorators import action

class BoardViewSet(viewsets.ModelViewSet):
    """
    ViewSet für Board-Management (alternative zu den oben genannten Views).
    Nur falls Sie ViewSet-basierte URLs verwenden.
    """
    serializer_class = BoardDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return boards where user is owner or member."""
        user = self.request.user
        return Board.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

    def perform_create(self, serializer):
        """Create board with current user as owner."""
        board = serializer.save(owner=self.request.user)
        board.members.add(self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Override destroy to add custom logic."""
        instance = self.get_object()
        if instance.owner != request.user:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def user_boards(self, request):
        """Get all boards for current user."""
        boards = self.get_queryset()
        serializer = BoardListSerializer(boards, many=True)
        return Response(serializer.data)