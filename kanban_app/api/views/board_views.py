from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.db import transaction, models
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.utils.dateparse import parse_datetime
import logging
import traceback

from kanban_app.models import Board, BoardMembership, Column
from ..serializers.board_serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
    BoardMembershipSerializer
)
from ..permissions import IsOwnerOrMember

logger = logging.getLogger(__name__)


class BoardListCreateView(ListCreateAPIView):
    """List boards or create a new board."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BoardDetailSerializer
        return BoardListSerializer

    def get_queryset(self):
        """Return boards where user is owner or member."""
        user = self.request.user
        return Board.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct().order_by('-created_at')

    def _validate_request_data(self, request_data):
        """Validate basic request data and convert title to name."""
        if not request_data:
            return None, "No data provided"
        
        # Make a mutable copy if needed
        if hasattr(request_data, '_mutable'):
            request_data._mutable = True
        
        title = request_data.get('title', '').strip()
        name = request_data.get('name', '').strip()
        
        if not title and not name:
            return None, "Board name/title is required"
        
        # Convert title to name if name is empty
        if title and not name:
            request_data['name'] = title
            logger.info(f"Converted 'title' to 'name': {title}")
        
        return request_data, None

    def _validate_members(self, members):
        """Validate members list format."""
        if not isinstance(members, list):
            return False, "Members must be a list"
        return True, None

    def _create_board_with_serializer(self, request):
        """Create board using serializer validation."""
        serializer = self.get_serializer(data=request.data)
        
        logger.error(f"Serializer class: {self.get_serializer_class()}")
        logger.error(f"Request data keys: {list(request.data.keys())}")
        logger.error(f"Request data values: {request.data}")
        
        if not serializer.is_valid():
            logger.error(f"Serializer validation errors: {serializer.errors}")
            logger.error(f"Serializer fields: {list(serializer.fields.keys())}")
            return None, {"error": "Validation failed", "details": serializer.errors}
        
        board = serializer.save(owner=request.user)
        logger.info(f"Board '{board.name}' created with ID: {board.id}")
        return board, None

    def _add_owner_as_admin(self, board, user):
        """Add board owner as ADMIN member."""
        BoardMembership.objects.create(
            user=user,
            board=board,
            role='ADMIN'
        )
        logger.info(f"Added {user} as ADMIN member to board {board.name}")

    def _create_default_columns(self, board):
        """Create default columns for the board."""
        default_columns = [
            ('To Do', 1),
            ('In Progress', 2),
            ('Review', 3),
            ('Done', 4)
        ]
        
        for col_name, position in default_columns:
            column = Column.objects.create(
                name=col_name,
                board=board,
                position=position
            )
            logger.info(f"Created column '{col_name}' (ID: {column.id}) for board {board.name}")

    def _add_member_by_email(self, email, board, owner_id):
        """Add a single member to board by email."""
        if not isinstance(email, str) or '@' not in email:
            logger.warning(f"Invalid member email: {email}")
            return
        
        try:
            from django.contrib.auth.models import User
            member_user = User.objects.get(email=email)
            if member_user.id != owner_id:  # Don't add owner again
                BoardMembership.objects.get_or_create(
                    user=member_user,
                    board=board,
                    defaults={'role': 'VIEWER'}
                )
                logger.info(f"Added {member_user.email} as VIEWER member to board {board.name}")
        except User.DoesNotExist:
            logger.warning(f"User with email {email} not found")
        except Exception as e:
            logger.error(f"Error adding member {email}: {str(e)}")

    def _add_board_members(self, members, board, owner_id):
        """Add all members to the board."""
        for member_email in members:
            self._add_member_by_email(member_email, board, owner_id)

    def _prepare_response_data(self, board):
        """Prepare and log response data."""
        detail_serializer = BoardDetailSerializer(board)
        response_data = detail_serializer.data
        logger.info(f"Board response data: {response_data}")
        return response_data

def create(self, request, *args, **kwargs):
    """Create a new board with default columns and members."""
    logger.error(f"=== BOARD CREATION DEBUG START ===")
    logger.error(f"User: {request.user}")
    logger.error(f"Is authenticated: {request.user.is_authenticated}")
    logger.error(f"Request method: {request.method}")
    logger.error(f"Request data: {request.data}")
    
    try:
        # Validate and create board
        request_data, error = self._validate_request_data(request.data)
        logger.error(f"Validation result - data: {request_data}, error: {error}")
        
        if error:
            logger.error(f"Validation error: {error}")
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        # Create board with serializer
        board, board_error = self._create_board_with_serializer(request)
        logger.error(f"Board creation result - board: {board}, error: {board_error}")
        
        if board_error:
            logger.error(f"Board creation error: {board_error}")
            return Response(board_error, status=status.HTTP_400_BAD_REQUEST)

        # CRITICAL FIX: Add owner as admin and create default columns IN THE SAME TRANSACTION
        with transaction.atomic():
            # Add owner as admin member
            self._add_owner_as_admin(board, request.user)
            logger.error(f"Owner added as admin")
            
            # Create default columns - THIS IS THE MISSING PART
            self._create_default_columns(board)
            logger.error(f"Default columns created")
            
            # Verify columns were created
            columns_count = board.columns.count()
            logger.error(f"Columns created count: {columns_count}")
            
            # Process members if provided
            members = request_data.get('members', [])
            if members:
                self._validate_members(members)
                for member_data in members:
                    if isinstance(member_data, int):
                        try:
                            from django.contrib.auth.models import User
                            user = User.objects.get(id=member_data)
                            self._add_member_by_email(user.email, board, request.user.id)
                        except User.DoesNotExist:
                            logger.warning(f"User with ID {member_data} not found")

        # Refresh board from database to get all relationships
        board.refresh_from_db()
        
        # Return detailed board data with columns
        detail_serializer = BoardDetailSerializer(board)
        response_data = detail_serializer.data
        logger.error(f"Final response data: {response_data}")
        logger.error(f"Final columns count: {len(response_data.get('columns', []))}")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Board creation error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response(
            {"error": "Internal server error", "details": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
            
            
class BoardDetailView(RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a board."""
    serializer_class = BoardDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrMember]
    lookup_field = "pk"

    def get_queryset(self):
        """Return boards where user is owner or member."""
        user = self.request.user
        return Board.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            response_data = serializer.data
            
            logger.info("=== BOARD RETRIEVAL DEBUG ===")
            logger.info(f"Board ID: {response_data.get('id')}")
            logger.info(f"Board Name: {response_data.get('name')}")
            logger.info(f"Board Description: {response_data.get('description')}")
            logger.info(f"Board Status: {response_data.get('status')}")
            logger.info(f"Board Deadline: {response_data.get('deadline')}")
            logger.info(f"Owner: {response_data.get('owner')}")
            logger.info(f"Members count: {len(response_data.get('members', []))}")
            logger.info(f"Columns count: {len(response_data.get('columns', []))}")
            logger.info(f"Full response keys: {list(response_data.keys())}")
            logger.info("=== END DEBUG ===")
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Board retrieval error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": "Failed to retrieve board", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        try:
            deadline_str = request.data.get('deadline')
            if deadline_str:
                try:
                    deadline = parse_datetime(deadline_str)
                    if not deadline:
                        return Response(
                            {"error": "Invalid deadline format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    request.data['deadline'] = deadline
                except ValueError:
                    return Response(
                        {"error": "Invalid deadline format"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            board_status = request.data.get('status')
            if board_status:
                valid_statuses = ['PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED']
                if board_status not in valid_statuses:
                    return Response(
                        {"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            return super().update(request, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Board update error: {str(e)}")
            return Response(
                {"error": "Failed to update board", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BoardMembersView(ListAPIView):
    """List members of a specific board."""
    serializer_class = BoardMembershipSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        board_id = self.kwargs.get("board_id")
        board = get_object_or_404(Board, pk=board_id)
        
        user = self.request.user
        if not Board.objects.filter(
            models.Q(owner=user) | models.Q(members=user),
            pk=board_id
        ).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to view this board's members")
        
        return BoardMembership.objects.filter(board=board)