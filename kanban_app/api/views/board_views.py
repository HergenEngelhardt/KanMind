from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth.models import User
import logging

from kanban_app.models import Board, BoardMembership
from kanban_app.api.serializers.board_serializers import (
    BoardListSerializer, 
    BoardDetailSerializer, 
    BoardCreateSerializer
)

logger = logging.getLogger(__name__)


class BoardViewSet(viewsets.ModelViewSet):
    """
    ViewSet für Board-Management mit optimiertem Caching.
    
    Supports CRUD operations for boards with member management.
    Only owners and members can access boards.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BoardListSerializer
        elif self.action == 'create':
            return BoardCreateSerializer
        else:
            return BoardDetailSerializer
    
    def get_queryset(self):
        """Optimierte Query mit select_related und prefetch_related."""
        return Board.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).select_related('owner').prefetch_related(
            'members',
            'columns',
            'columns__tasks',
            'columns__tasks__assignee',
            'columns__tasks__reviewers'
        ).distinct()

    @method_decorator(cache_page(30))  
    def list(self, request, *args, **kwargs):
        """List Boards mit Caching."""
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60))  
    def retrieve(self, request, *args, **kwargs):
        """Retrieve einzelnes Board mit Caching."""
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create new board with automatic owner membership."""
        logger.info(f"Board creation request from user: {request.user.username}")
        logger.info(f"Request data: {request.data}")
    
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            board = serializer.save(owner=request.user)
            
            membership, created = BoardMembership.objects.get_or_create(
                board=board,
                user=request.user,
                defaults={'role': 'ADMIN'}
            )
            if created:
                logger.info(f"Added {request.user.username} as ADMIN member to board {board.title}")
            else:
                logger.info(f"User {request.user.username} already member of board {board.title}")
            
            member_ids = request.data.get('members', [])
            for member_id in member_ids:
                if member_id != request.user.id:
                    try:
                        member_user = User.objects.get(id=member_id)
                        membership, created = BoardMembership.objects.get_or_create(
                            board=board,
                            user=member_user,
                            defaults={'role': 'EDITOR'}
                        )
                        if created:
                            logger.info(f"Added {member_user.username} as EDITOR member to board {board.title}")
                        else:
                            logger.info(f"User {member_user.username} already member of board {board.title}")
                    except User.DoesNotExist:
                        logger.warning(f"User with ID {member_id} not found")
            
            logger.info("Board created successfully")
            
            detail_serializer = BoardDetailSerializer(board)
            response_data = detail_serializer.data
            logger.info(f"Board response data: {response_data}")
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"Board creation validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request, *args, **kwargs):
        """Update board - only owners can update."""
        board = self.get_object()
        
        if board.owner != request.user:
            return Response(
                {"error": "Only board owners can update the board"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        cache_key = f"board_detail_{board.id}"
        cache.delete(cache_key)
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete board - only owners can delete."""
        board = self.get_object()
        
        if board.owner != request.user:
            return Response(
                {"error": "Only board owners can delete the board"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        cache_key = f"board_detail_{board.id}"
        cache.delete(cache_key)
        
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add member to board."""
        board = self.get_object()
        
        if board.owner != request.user:
            return Response(
                {"error": "Only board owners can add members"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'VIEWER')
        
        try:
            user = User.objects.get(id=user_id)
            membership, created = BoardMembership.objects.get_or_create(
                board=board,
                user=user,
                defaults={'role': role}
            )
            
            if not created:
                membership.role = role
                membership.save()
            
            cache_key = f"board_detail_{board.id}"
            cache.delete(cache_key)
            
            return Response({"message": "Member added successfully"})
        
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove member from board."""
        board = self.get_object()
        
        if board.owner != request.user:
            return Response(
                {"error": "Only board owners can remove members"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            if user == board.owner:
                return Response(
                    {"error": "Cannot remove board owner"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            BoardMembership.objects.filter(board=board, user=user).delete()
            
            cache_key = f"board_detail_{board.id}"
            cache.delete(cache_key)
            
            return Response({"message": "Member removed successfully"})
        
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Optimierte Detail-View für einzelne Boards.
    """
    serializer_class = BoardDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Optimierte Query mit Prefetching."""
        return Board.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).select_related('owner').prefetch_related(
            'members',
            'columns',
            'columns__tasks',
            'columns__tasks__assignee',
            'columns__tasks__reviewers'
        ).distinct()
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve board mit Response Caching."""
        try:
            instance = self.get_object()
            
            cache_key = f"board_detail_{instance.id}_{instance.updated_at.timestamp()}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return Response(cached_data)
            
            serializer = self.get_serializer(instance)
            data = serializer.data
            
            cache.set(cache_key, data, 300)
            
            if not hasattr(request, '_logged_board_access'):
                logger.warning(f"Board {instance.id} accessed by user {request.user.username}")
                request._logged_board_access = True
                
            return Response(data)
            
        except Exception as e:
            logger.error(f"Board retrieval error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            raise

    def update(self, request, *args, **kwargs):
        """Update mit Cache-Clearing."""
        instance = self.get_object()
        
        if instance.owner != request.user:
            return Response(
                {"error": "Only board owners can update the board"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        cache_pattern = f"board_detail_{instance.id}_*"
        cache.delete_many([cache_pattern])
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete mit Cache-Clearing."""
        instance = self.get_object()
        
        if instance.owner != request.user:
            return Response(
                {"error": "Only board owners can delete the board"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        cache_pattern = f"board_detail_{instance.id}_*"
        cache.delete_many([cache_pattern])
        
        return super().destroy(request, *args, **kwargs)