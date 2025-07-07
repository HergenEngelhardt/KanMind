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
import json

logger = logging.getLogger(__name__)


class BoardListCreateView(ListCreateAPIView):
    """
    List user's boards or create a new board.

    GET: Returns boards where user is owner or member
    POST: Creates new board with authenticated user as owner
    """
    serializer_class = BoardListSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get boards where user is owner or member."""
        user = self.request.user
        if not user.is_authenticated:
            return Board.objects.none()

        owned_boards = Board.objects.filter(owner=user)
        for board in owned_boards:
            if not board.members.filter(id=user.id).exists():
                from kanban_app.models import BoardMembership
                BoardMembership.objects.get_or_create(
                    user=user,
                    board=board,
                    defaults={'role': 'ADMIN'}
                )

        return Board.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

    def get_permissions(self):
        """Set permissions based on request method."""
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Create board and add owner as member."""
        board = serializer.save(owner=self.request.user)
        self._add_owner_as_member(board)
        
        # Ensure the board is properly saved after adding membership
        board.refresh_from_db()

    def create(self, request, *args, **kwargs):
        """Override create to handle title->name conversion and add error handling."""
        if not request.user.is_authenticated:
            logger.error("User not authenticated")
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        logger.info(f"Board creation request from user: {request.user}")
        logger.info(f"Request data: {request.data}")

        data = request.data.copy() if hasattr(
            request.data, 'copy') else dict(request.data)

        if 'title' in data and 'name' not in data:
            data['name'] = data['title']
            logger.info(f"Converted 'title' to 'name': {data['title']}")

        if 'title' in data:
            del data['title']

        if not data.get('name', '').strip():
            logger.error("Name field missing or empty")
            return Response(
                {"error": "Board name is required and cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=data)

        try:
            if serializer.is_valid():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                logger.info("Board created successfully")
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED,
                    headers=headers
                )
            else:
                logger.error(
                    f"Serializer validation failed: {serializer.errors}")
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f"Board creation error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            return Response(
                {"error": f"Board creation failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _add_owner_as_member(self, board):
        """Add board owner as member if not already added."""
        from kanban_app.models import BoardMembership
        membership, created = BoardMembership.objects.get_or_create(
            user=self.request.user,
            board=board,
            defaults={'role': 'ADMIN'}
        )
        if created:
            logger.info(f"Added {self.request.user} as ADMIN member to board {board.name}")
        else:
            logger.info(f"User {self.request.user} already member of board {board.name}")


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
        """Return user information response with robust fullname."""
        first_name = (user.first_name or "").strip()
        last_name = (user.last_name or "").strip()
        
        if first_name and last_name:
            fullname = f"{first_name} {last_name}"
        elif first_name:
            fullname = first_name
        elif last_name:
            fullname = last_name
        else:
            fullname = user.email.split('@')[0] if user.email else "User"
        
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "fullname": fullname,
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
    Reorder tasks within or between columns.

    Expects task reordering data with permission validation.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Handle task reordering."""
        return Response({"message": "Task reordering not implemented yet"})