import logging
import traceback
from django.db import models, transaction
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from kanban_app.models import Board, BoardMembership
from kanban_app.api.serializers.board_serializers import BoardListSerializer, BoardDetailSerializer
from kanban_app.api.permissions import IsOwnerOrMember, IsOwner

logger = logging.getLogger(__name__)


class BoardListCreateView(ListCreateAPIView):
    """List boards or create a new board."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BoardListSerializer
        return BoardListSerializer

    def get_queryset(self):
        try:
            user = self.request.user
            return Board.objects.filter(
                models.Q(owner=user) | models.Q(members=user)
            ).distinct().select_related('owner').prefetch_related(
                'boardmembership_set__user'
            ).order_by('-created_at')
        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            return Board.objects.none()

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

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing boards: {str(e)}")
            return Response(
                {"error": "Failed to retrieve boards"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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


class BoardMembersView(ListCreateAPIView):
    """Manage board members."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        board_id = self.kwargs['pk']
        return BoardMembership.objects.filter(board_id=board_id).select_related('user', 'board')

    def get_serializer_class(self):
        from kanban_app.api.serializers.board_serializers import BoardMembershipSerializer
        return BoardMembershipSerializer

    def perform_create(self, serializer):
        board_id = self.kwargs['pk']
        try:
            board = Board.objects.get(id=board_id)
            self.check_object_permissions(self.request, board)
            serializer.save(board=board)
        except Board.DoesNotExist:
            raise NotFound("Board not found")