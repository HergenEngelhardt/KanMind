import logging
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.contrib.auth.models import User
from kanban_app.models import Board
from kanban_app.api.serializers.board_serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
)
from kanban_app.api.serializers.user_serializers import UserSerializer
from kanban_app.api.permissions import IsOwnerOrMember, IsOwner

logger = logging.getLogger(__name__)


class BoardListCreateView(ListCreateAPIView):
    """List user's boards or create a new board."""
    serializer_class = BoardListSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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

    def perform_create(self, serializer):
        board = serializer.save(owner=self.request.user)
        self._add_owner_as_member(board)
        board.refresh_from_db()

    def _add_owner_as_member(self, board):
        from kanban_app.models import BoardMembership
        BoardMembership.objects.get_or_create(
            user=self.request.user,
            board=board,
            defaults={'role': 'ADMIN'}
        )


class BoardDetailView(RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a specific board."""
    serializer_class = BoardDetailSerializer
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsOwner()]
        return [IsOwnerOrMember()]

    def get_queryset(self): 
        try:
            return Board.objects.select_related('owner').prefetch_related(
                'boardmembership_set__user',
                'columns__tasks__assignee',
                'columns__tasks__reviewers'
            ).all()
        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            return Board.objects.all()

    def get_object(self):
        try:
            obj = super().get_object()
            # Check permissions
            self.check_object_permissions(self.request, obj)
            return obj
        except Exception as e:
            logger.error(f"Error getting object: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get(self, request, *args, **kwargs):
        try:
            board = self.get_object()
            serializer = self.get_serializer(board)
            
            # Debug logging
            logger.info("=== BOARD RETRIEVAL DEBUG ===")
            logger.info(f"Board ID: {board.id}")
            logger.info(f"Board Name: {board.name}")
            logger.info(f"Request User: {request.user}")
            logger.info(f"Board Owner: {board.owner}")
            logger.info("=== END DEBUG ===")
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Board retrieval error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Request User: {request.user}")
            logger.error(f"Is Authenticated: {request.user.is_authenticated}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            if isinstance(e, (PermissionDenied, NotFound)):
                raise
            
            return Response(
                {"error": "Internal server error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)
        return Response(
            {"message": "Board successfully deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )


class BoardMembersView(APIView):
    """Get all members of a board for task assignment."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            board = Board.objects.get(pk=pk)
            
            user_is_member = (
                board.owner == request.user or 
                board.boardmembership_set.filter(user=request.user).exists()
            )
            
            if not user_is_member:
                raise PermissionDenied("You don't have permission to view board members")
            
            members = []
            
            owner_data = UserSerializer(board.owner).data
            owner_data['role'] = 'OWNER'
            members.append(owner_data)
            
            for membership in board.boardmembership_set.all():
                if membership.user != board.owner:
                    user_data = UserSerializer(membership.user).data
                    user_data['role'] = membership.role
                    members.append(user_data)
            
            return Response(members, status=status.HTTP_200_OK)
            
        except Board.DoesNotExist:
            raise NotFound("Board not found")