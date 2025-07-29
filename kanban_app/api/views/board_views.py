from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth.models import User

from kanban_app.models import Board, BoardMembership, Column
from kanban_app.api.serializers.board_serializers import (
    BoardListSerializer, 
    BoardDetailSerializer, 
    BoardCreateSerializer
)


class BoardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Board CRUD operations.
    
    Provides complete board management functionality including creation,
    retrieval, updating, and deletion with proper authentication and permissions.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        
        Returns:
            Serializer: The serializer class for the current action
        """
        if self.action == 'list':
            return BoardListSerializer
        elif self.action == 'create':
            return BoardCreateSerializer
        return BoardDetailSerializer

    def get_queryset(self):
        """
        Get the queryset of boards accessible to the current user.
        
        Returns:
            QuerySet: Boards where user is owner or member
        """
        user = self.request.user
        return Board.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().select_related('owner').prefetch_related('members', 'columns')

    def create(self, request, *args, **kwargs):
        """
        Create a new board with default columns and members.
        
        Args:
            request: HTTP request object containing board data
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Created board data with status 201 or error with status 400
        """
        try:
            data = self._prepare_board_data(request.data)
            board = self._create_board_with_validation(data, request.user)
            self._setup_board_defaults(board, request.data.get('members', []))
            
            response_serializer = BoardDetailSerializer(board)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception:
            return Response(
                {"error": "Could not create board"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def _prepare_board_data(self, request_data):
        """
        Prepare and normalize board data for creation.
        
        Args:
            request_data (dict): Raw request data
            
        Returns:
            dict: Normalized board data
        """
        data = request_data.copy()
        if 'title' in data and 'name' not in data:
            data['name'] = data['title']
        return data

    def _create_board_with_validation(self, data, owner):
        """
        Create board after validating data.
        
        Args:
            data (dict): Board creation data
            owner (User): Board owner
            
        Returns:
            Board: Created board instance
            
        Raises:
            ValidationError: If data is invalid
        """
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save(owner=owner)

    def _setup_board_defaults(self, board, member_ids):
        """
        Setup default columns and members for the board.
        
        Args:
            board (Board): Created board instance
            member_ids (list): List of member user IDs
        """
        self._create_default_columns(board)
        self._add_board_members(board, member_ids)
        self._add_owner_as_admin(board)

    def _create_default_columns(self, board):
        """
        Create default Kanban columns for the board.
        
        Args:
            board (Board): Board instance to add columns to
        """
        default_columns = [
            {'title': 'To-do', 'position': 0},
            {'title': 'In-progress', 'position': 1},
            {'title': 'Review', 'position': 2},
            {'title': 'Done', 'position': 3},
        ]
        
        for col_data in default_columns:
            Column.objects.create(
                board=board,
                title=col_data['title'],
                position=col_data['position']
            )

    def _add_board_members(self, board, member_ids):
        """
        Add members to the board with editor role.
        
        Args:
            board (Board): Board instance
            member_ids (list): List of user IDs to add as members
        """
        for member_id in member_ids:
            try:
                user = User.objects.get(id=member_id)
                if user != board.owner:
                    BoardMembership.objects.get_or_create(
                        user=user,
                        board=board,
                        defaults={'role': 'EDITOR'}
                    )
            except User.DoesNotExist:
                continue

    def _add_owner_as_admin(self, board):
        """
        Add board owner as admin member.
        
        Args:
            board (Board): Board instance
        """
        BoardMembership.objects.get_or_create(
            user=board.owner,
            board=board,
            defaults={'role': 'ADMIN'}
        )

    def update(self, request, *args, **kwargs):
        """
        Update an existing board.
        
        Args:
            request: HTTP request object containing update data
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Updated board data or error response
        """
        try:
            instance = self.get_object()
            
            if not self._user_can_update_board(instance, request.user):
                return Response(
                    {"error": "Only board owners can update the board"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            self._process_board_update(instance, request.data)
            return Response(self.get_serializer(instance).data)
            
        except Exception:
            return Response(
                {"error": "Could not update board"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def _user_can_update_board(self, board, user):
        """
        Check if user has permission to update the board.
        
        Args:
            board (Board): Board instance
            user (User): User attempting to update
            
        Returns:
            bool: True if user can update, False otherwise
        """
        return board.owner == user

    def _process_board_update(self, instance, request_data):
        """
        Process board update including members management.
        
        Args:
            instance (Board): Board instance to update
            request_data (dict): Update data from request
        """
        data = request_data.copy()
        
        if 'members' in data:
            member_ids = data.pop('members')
            self._update_board_members(instance, member_ids)
        
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def _update_board_members(self, board, member_ids):
        """
        Update board members list.
        
        Args:
            board (Board): Board instance
            member_ids (list): New list of member IDs
        """
        BoardMembership.objects.filter(board=board).exclude(user=board.owner).delete()
        self._add_board_members(board, member_ids)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a board.
        
        Args:
            request: HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Empty response with status 204 or error response
        """
        try:
            instance = self.get_object()
            
            if not self._user_can_delete_board(instance, request.user):
                return Response(
                    {"error": "Only board owners can delete the board"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception:
            return Response(
                {"error": "Could not delete board"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def _user_can_delete_board(self, board, user):
        """
        Check if user has permission to delete the board.
        
        Args:
            board (Board): Board instance
            user (User): User attempting to delete
            
        Returns:
            bool: True if user can delete, False otherwise
        """
        return board.owner == user