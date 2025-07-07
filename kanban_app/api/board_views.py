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
from kanban_app.api.serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
    UserSerializer,
)
from kanban_app.api.permissions import IsOwnerOrMember, IsOwner


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
        return Board.objects.select_related('owner').prefetch_related(
            'boardmembership_set__user',
            'columns__tasks__assignee',
            'columns__tasks__reviewers'
        ).all()

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