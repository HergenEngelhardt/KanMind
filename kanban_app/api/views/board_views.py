"""
Board management views for Kanban board operations.

This module provides CRUD operations for boards including creation,
retrieval, updating, and deletion with proper permissions and validation.
"""

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
    ViewSet for managing Board CRUD operations with authentication.
    
    Provides complete board management functionality including creation,
    retrieval, updating, and deletion with proper authentication and permissions.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        
        Returns:
            Serializer: Serializer class for current action
        """
        serializer_map = {
            'list': BoardListSerializer,
            'create': BoardCreateSerializer,
        }
        return serializer_map.get(self.action, BoardDetailSerializer)

    def get_queryset(self):
        """
        Return boards accessible to current user.
        
        Returns:
            QuerySet: Boards where user is owner or member
        """
        user = self.request.user
        return Board.objects.filter(
            Q(owner=user) | Q(boardmembership__user=user)
        ).distinct()

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve specific board with detailed information.
        
        Args:
            request (Request): HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments containing board pk
            
        Returns:
            Response: Board detail data or error response
            
        Raises:
            Http404: If board not found or access denied
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Board.DoesNotExist:
            return self._board_not_found_error()

    def create(self, request, *args, **kwargs):
        """
        Create new board with default columns and members.
        
        Args:
            request (Request): HTTP request containing board data
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Created board data or error response
            
        Raises:
            ValidationError: If board data is invalid
        """
        try:
            return self._create_board_with_setup(request)
        except Exception:
            return self._board_creation_error()

    def update(self, request, *args, **kwargs):
        """
        Update existing board with permission validation.
        
        Args:
            request (Request): HTTP request containing update data
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Updated board data or error response
            
        Raises:
            PermissionDenied: If user cannot update board
        """
        try:
            return self._update_board_with_validation(request)
        except Exception:
            return self._board_update_error()

    def destroy(self, request, *args, **kwargs):
        """
        Delete existing board with permission validation.
        
        Args:
            request (Request): HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Success or error response
            
        Raises:
            PermissionDenied: If user cannot delete board
        """
        try:
            return self._delete_board_with_validation(request)
        except Exception:
            return self._board_deletion_error()

    def _create_board_with_setup(self, request):
        """
        Create board with validation and default setup.
        
        Args:
            request (Request): HTTP request with board data
            
        Returns:
            Response: Created board response
        """
        data = self._prepare_board_data(request.data)
        board = self._create_validated_board(data, request.user)
        self._setup_board_defaults(board, request.data.get('members', []))
        
        response_serializer = BoardDetailSerializer(board)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def _update_board_with_validation(self, request):
        """
        Update board with permission validation.
        
        Args:
            request (Request): HTTP request with update data
            
        Returns:
            Response: Updated board response
        """
        instance = self.get_object()
        
        if not self._user_can_update_board(instance, request.user):
            return self._permission_denied_error("update")
        
        self._process_board_update(instance, request.data)
        return Response(self.get_serializer(instance).data)

    def _delete_board_with_validation(self, request):
        """
        Delete board with permission validation.
        
        Args:
            request (Request): HTTP request object
            
        Returns:
            Response: Deletion success response
        """
        instance = self.get_object()
        
        if not self._user_can_delete_board(instance, request.user):
            return self._permission_denied_error("delete")
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _prepare_board_data(self, request_data):
        """
        Prepare and normalize board data for creation.
        
        Args:
            request_data (dict): Raw request data
            
        Returns:
            dict: Normalized board data with proper field names
        """
        data = request_data.copy()
        if 'title' in data and 'name' not in data:
            data['name'] = data['title']
        return data

    def _create_validated_board(self, data, owner):
        """
        Create board after data validation.
        
        Args:
            data (dict): Board creation data
            owner (User): Board owner
            
        Returns:
            Board: Created board instance
            
        Raises:
            ValidationError: If data validation fails
        """
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.save(owner=owner)

    def _setup_board_defaults(self, board, member_ids):
        """
        Setup default columns and members for board.
        
        Args:
            board (Board): Created board instance
            member_ids (list): List of member user IDs
        """
        self._create_default_columns(board)
        self._add_board_members(board, member_ids)
        self._add_owner_as_admin(board)

    def _create_default_columns(self, board):
        """
        Create default Kanban columns for board.
        
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
            self._create_single_column(board, col_data)

    def _create_single_column(self, board, col_data):
        """
        Create single column for board.
        
        Args:
            board (Board): Board instance
            col_data (dict): Column data with title and position
        """
        Column.objects.create(
            board=board,
            title=col_data['title'],
            position=col_data['position']
        )

    def _add_board_members(self, board, member_ids):
        """
        Add members to board with editor role.
        
        Args:
            board (Board): Board instance
            member_ids (list): List of user IDs to add as members
        """
        for member_id in member_ids:
            self._add_single_member(board, member_id)

    def _add_single_member(self, board, member_id):
        """
        Add single member to board if valid.
        
        Args:
            board (Board): Board instance
            member_id (int): User ID to add as member
        """
        try:
            user = User.objects.get(id=member_id)
            if user != board.owner:
                BoardMembership.objects.get_or_create(
                    user=user,
                    board=board,
                    defaults={'role': 'EDITOR'}
                )
        except User.DoesNotExist:
            pass

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

    def _user_can_update_board(self, board, user):
        """
        Check if user has permission to update board.
        
        Args:
            board (Board): Board instance
            user (User): User attempting to update
            
        Returns:
            bool: True if user can update, False otherwise
        """
        return board.owner == user

    def _user_can_delete_board(self, board, user):
        """
        Check if user has permission to delete board.
        
        Args:
            board (Board): Board instance
            user (User): User attempting to delete
            
        Returns:
            bool: True if user can delete, False otherwise
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
        
        self._update_board_fields(instance, data)

    def _update_board_fields(self, instance, data):
        """
        Update board fields with validation.
        
        Args:
            instance (Board): Board instance to update
            data (dict): Update data
        """
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def _update_board_members(self, board, member_ids):
        """
        Update board members list by replacing existing.
        
        Args:
            board (Board): Board instance
            member_ids (list): New list of member IDs
        """
        BoardMembership.objects.filter(board=board).exclude(user=board.owner).delete()
        self._add_board_members(board, member_ids)

    def _board_not_found_error(self):
        """
        Create board not found error response.
        
        Returns:
            Response: HTTP 404 response for board not found
        """
        return Response(
            {"error": "Board not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    def _board_creation_error(self):
        """
        Create board creation error response.
        
        Returns:
            Response: HTTP 400 response for creation failure
        """
        return Response(
            {"error": "Could not create board"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    def _board_update_error(self):
        """
        Create board update error response.
        
        Returns:
            Response: HTTP 400 response for update failure
        """
        return Response(
            {"error": "Could not update board"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    def _board_deletion_error(self):
        """
        Create board deletion error response.
        
        Returns:
            Response: HTTP 400 response for deletion failure
        """
        return Response(
            {"error": "Could not delete board"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    def _permission_denied_error(self, action):
        """
        Create permission denied error response.
        
        Args:
            action (str): Action being attempted
            
        Returns:
            Response: HTTP 403 response for permission denied
        """
        return Response(
            {"error": f"Only board owners can {action} the board"}, 
            status=status.HTTP_403_FORBIDDEN
        )