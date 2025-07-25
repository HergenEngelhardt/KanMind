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
    ViewSet for managing Board operations.
    
    Provides CRUD operations for Board models with authentication and 
    permission controls for board owners and members.
    """
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        
        Returns:
            type: Serializer class for the current action
        """
        if self.action == 'list':
            return BoardListSerializer
        elif self.action == 'create':
            return BoardCreateSerializer
        else:
            return BoardDetailSerializer
    
    def get_queryset(self):
        """
        Return boards where user is owner or member.
        
        Returns:
            QuerySet: Filtered Board queryset with related data prefetched
        """
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
        """
        Retrieve a specific board.
        
        Args:
            request: HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Board data or error message
            
        Raises:
            Exception: When board is not found
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception:
            return Response(
                {"error": "Board not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    def create(self, request, *args, **kwargs):
        """
        Create a new board.
        
        Args:
            request: HTTP request object containing board data
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Created board data or error message
            
        Raises:
            Exception: When board creation fails
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            board = serializer.save()
            
            response_serializer = BoardDetailSerializer(board, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception:
            return Response(
                {"error": "Could not create board"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def _update_board_members(self, instance, member_ids):
        """
        Update board members based on provided member IDs.
        
        Args:
            instance (Board): Board instance to update
            member_ids (list): List of user IDs to add as members
        """
        BoardMembership.objects.filter(board=instance).exclude(user=instance.owner).delete()
        
        for member_id in member_ids:
            try:
                user = User.objects.get(id=member_id)
                if user != instance.owner:
                    BoardMembership.objects.get_or_create(
                        user=user,
                        board=instance,
                        defaults={'role': 'EDITOR'}
                    )
            except User.DoesNotExist:
                continue

    def update(self, request, *args, **kwargs):
        """
        Update an existing board.
        
        Args:
            request: HTTP request object containing updated board data
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Updated board data or error message
            
        Raises:
            Exception: When board update fails
        """
        try:
            instance = self.get_object()
            
            if instance.owner != request.user:
                return Response(
                    {"error": "Only board owners can update the board"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            data = request.data.copy()
            if 'members' in data:
                member_ids = data.pop('members')
                self._update_board_members(instance, member_ids)
            
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(serializer.data)
        except Exception:
            return Response(
                {"error": "Could not update board"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """
        Delete a board.
        
        Args:
            request: HTTP request object
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Empty response or error message
            
        Raises:
            Exception: When board deletion fails
        """
        try:
            instance = self.get_object()
            
            if instance.owner != request.user:
                return Response(
                    {"error": "Only board owners can delete the board"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response(
                {"error": "Could not delete board"}, 
                status=status.HTTP_400_BAD_REQUEST
            )