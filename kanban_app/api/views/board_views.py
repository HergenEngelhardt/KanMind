from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction, models
from django.shortcuts import get_object_or_404
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
    queryset = Board.objects.all()
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
        """Create a new board with default columns and members."""
        logger.info(f"=== BOARD CREATION START ===")
        logger.info(f"User: {request.user}")
        logger.info(f"Request data: {request.data}")
        
        try:
            data = request.data.copy()
            if not data.get('title', '').strip():
                return Response(
                    {"error": "Board title is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                serializer = self.get_serializer(data=data)
                if not serializer.is_valid():
                    logger.error(f"Serializer errors: {serializer.errors}")
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                board = serializer.save(owner=request.user)
                logger.info(f"Board '{board.title}' created with ID: {board.id}")

                BoardMembership.objects.create(
                    user=request.user,
                    board=board,
                    role='ADMIN'
                )
                logger.info(f"Added {request.user} as ADMIN member")

                default_columns = [
                    ('To Do', 1),
                    ('In Progress', 2),
                    ('Review', 3),
                    ('Done', 4)
                ]
                
                created_columns = []
                for col_title, position in default_columns:
                    column = Column.objects.create(
                        title=col_title,
                        board=board,
                        position=position
                    )
                    created_columns.append(column)
                    logger.info(f"✅ Created column '{col_title}' (ID: {column.id})")

                members = data.get('members', [])
                if members and isinstance(members, list):
                    for member_data in members:
                        if isinstance(member_data, int):
                            try:
                                from django.contrib.auth.models import User
                                user = User.objects.get(id=member_data)
                                if user.id != request.user.id:
                                    BoardMembership.objects.get_or_create(
                                        user=user,
                                        board=board,
                                        defaults={'role': 'VIEWER'}
                                    )
                                    logger.info(f"Added {user.email} as VIEWER member")
                            except User.DoesNotExist:
                                logger.warning(f"User with ID {member_data} not found")

                board.refresh_from_db()
                detail_serializer = BoardDetailSerializer(board)
                response_data = detail_serializer.data
                
                columns_count = len(response_data.get('columns', []))
                logger.info(f"Board creation SUCCESS! Columns count: {columns_count}")
                logger.info(f"Created columns: {[col.title for col in created_columns]}")
                
                if columns_count == 0:
                    logger.error(f"CRITICAL: No columns in response! Expected 4, got {columns_count}")
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Board creation error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": "Failed to create board", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BoardDetailView(RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a board."""
    queryset = Board.objects.all()
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
            
            columns_count = len(response_data.get('columns', []))
            logger.info(f"Board {instance.id} retrieved - Columns: {columns_count}")
            
            if columns_count == 0:
                logger.warning(f"Board {instance.id} has no columns!")
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Board retrieval error: {str(e)}")
            return Response(
                {"error": "Failed to retrieve board", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BoardMembersView(ListAPIView):
    """List board members."""
    queryset = BoardMembership.objects.all()
    serializer_class = BoardMembershipSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        board_id = self.kwargs.get('pk')
        return BoardMembership.objects.filter(board_id=board_id)