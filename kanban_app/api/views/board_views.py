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

from kanban_app.models import Board, BoardMembership
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

    def create(self, request, *args, **kwargs):
        try:
            logger.info(f"Board creation request from user: {request.user}")
            logger.info(f"Request data: {request.data}")
            
            if not request.data:
                return Response(
                    {"error": "No data provided"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            title = request.data.get('title', '').strip()
            name = request.data.get('name', '').strip()
            
            if not title and not name:
                return Response(
                    {"error": "Board name/title is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if title and not name:
                request.data['name'] = title
                logger.info(f"Converted 'title' to 'name': {title}")
            
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
            
            valid_statuses = ['PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED']
            board_status = request.data.get('status', 'PLANNING')
            if board_status not in valid_statuses:
                return Response(
                    {"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            members = request.data.get('members', [])
            if not isinstance(members, list):
                return Response(
                    {"error": "Members must be a list"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = self.get_serializer(data=request.data)
            
            if not serializer.is_valid():
                logger.error(f"Serializer validation errors: {serializer.errors}")
                return Response(
                    {"error": "Validation failed", "details": serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                board = serializer.save(owner=request.user)
                
                BoardMembership.objects.create(
                    user=request.user,
                    board=board,
                    role='ADMIN'
                )
                logger.info(f"Added {request.user} as ADMIN member to board {board.name}")
                
                for member_id in members:
                    if member_id != request.user.id:
                        try:
                            from django.contrib.auth.models import User
                            member_user = User.objects.get(id=member_id)
                            BoardMembership.objects.get_or_create(
                                user=member_user,
                                board=board,
                                defaults={'role': 'VIEWER'}
                            )
                            logger.info(f"Added {member_user} as VIEWER member to board {board.name}")
                        except User.DoesNotExist:
                            logger.warning(f"User with ID {member_id} not found")
                
                logger.info("Board created successfully")
                
                detail_serializer = BoardDetailSerializer(board)
                response_data = detail_serializer.data
                
                logger.info(f"Board response data: {response_data}")
                
                return Response(
                    response_data,
                    status=status.HTTP_201_CREATED
                )
                
        except ValidationError as e:
            logger.error(f"Validation error in board creation: {str(e)}")
            return Response(
                {"error": "Validation error", "details": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in board creation: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
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