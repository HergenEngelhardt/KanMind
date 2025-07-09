import logging
import traceback
from django.db import transaction
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from ...models import Board, BoardMembership, Column
from ..serializers.board_serializers import (
    BoardSerializer, 
    BoardDetailSerializer, 
    BoardCreateSerializer
)
from ..permissions import BoardPermission

logger = logging.getLogger('board_views')


class BoardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing boards.
    
    Provides CRUD operations for boards with proper permissions.
    Only allows users to see boards they are members of.
    """
    permission_classes = [IsAuthenticated, BoardPermission]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BoardCreateSerializer
        elif self.action in ['retrieve', 'list']:
            return BoardDetailSerializer
        return BoardSerializer
    
    def get_queryset(self):
        """Return boards where user is a member."""
        if not self.request.user.is_authenticated:
            return Board.objects.none()
        
        return Board.objects.filter(
            members__user=self.request.user
        ).distinct().prefetch_related(
            'members__user',
            'columns__tasks__assignee',
            'columns__tasks__created_by',
            'columns__tasks__reviewers'
        )

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
                for col_name, position in default_columns:
                    column = Column.objects.create(
                        name=col_name,  
                        board=board,
                        position=position
                    )
                    created_columns.append(column)
                    logger.info(f"Created column '{col_name}' (ID: {column.id})")

                members = data.get('members', [])
                if members and isinstance(members, list):
                    for member_data in members:
                        if isinstance(member_data, int):
                            try:
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
                
                columns_check = Column.objects.filter(board=board).count()
                logger.info(f"Columns in database after creation: {columns_check}")
                
                detail_serializer = BoardDetailSerializer(board, context={'request': request})
                response_data = detail_serializer.data
                
                columns_count = len(response_data.get('columns', []))
                logger.info(f"Board creation SUCCESS! Columns count in response: {columns_count}")
                logger.info(f"Created columns: {[col.name for col in created_columns]}")
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Board creation error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": "Failed to create board", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific board with detailed information."""
        try:
            instance = self.get_object()
            logger.info(f"=== BOARD RETRIEVAL DEBUG ===")
            logger.info(f"Board ID: {instance.id}")
            logger.info(f"Board Title: {instance.title}")
            logger.info(f"Board Description: {instance.description}")
            
            owner_data = None
            if instance.owner:
                from ..serializers.user_serializers import UserSerializer
                owner_data = UserSerializer(instance.owner).data
            logger.info(f"Owner: {owner_data}")
            
            members_count = instance.members.count()
            logger.info(f"Members count: {members_count}")
            
            columns_count = instance.columns.count()
            logger.info(f"Columns count: {columns_count}")
            
            serializer = self.get_serializer(instance)
            response_data = serializer.data
            
            logger.info(f"Full response keys: {list(response_data.keys())}")
            logger.info(f"=== END DEBUG ===")
            
            return Response(response_data)
        except Exception as e:
            logger.error(f"Board retrieval error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": "Failed to retrieve board"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """Update board details."""
        logger.info(f"Board update request from user: {request.user.email}")
        logger.info(f"Update data: {request.data}")
        
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Board update error: {str(e)}")
            return Response(
                {"error": "Failed to update board"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Delete a board (only owner can delete)."""
        logger.info(f"Board deletion request from user: {request.user.email}")
        
        try:
            board = self.get_object()
            if board.owner != request.user:
                return Response(
                    {"error": "Only the board owner can delete the board"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            logger.info(f"Deleting board: {board.title}")
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Board deletion error: {str(e)}")
            return Response(
                {"error": "Failed to delete board"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the board."""
        logger.info(f"Add member request from user: {request.user.email}")
        logger.info(f"Member data: {request.data}")
        
        try:
            board = self.get_object()
            user_id = request.data.get('user_id')
            role = request.data.get('role', 'VIEWER')
            
            if not user_id:
                return Response(
                    {"error": "user_id is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = User.objects.get(id=user_id)
            membership, created = BoardMembership.objects.get_or_create(
                user=user,
                board=board,
                defaults={'role': role}
            )
            
            if not created:
                membership.role = role
                membership.save()
                logger.info(f"Updated {user.email} role to {role}")
            else:
                logger.info(f"Added {user.email} as {role}")
            
            return Response({"message": "Member added successfully"})
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Add member error: {str(e)}")
            return Response(
                {"error": "Failed to add member"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the board."""
        logger.info(f"Remove member request from user: {request.user.email}")
        
        try:
            board = self.get_object()
            user_id = request.data.get('user_id')
            
            if not user_id:
                return Response(
                    {"error": "user_id is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = User.objects.get(id=user_id)
            
            if user == board.owner:
                return Response(
                    {"error": "Cannot remove board owner"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            BoardMembership.objects.filter(user=user, board=board).delete()
            logger.info(f"Removed {user.email} from board")
            
            return Response({"message": "Member removed successfully"})
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Remove member error: {str(e)}")
            return Response(
                {"error": "Failed to remove member"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )