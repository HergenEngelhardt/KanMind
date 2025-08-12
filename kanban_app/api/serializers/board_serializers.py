"""
Board serializers for the KanMind API.

This module contains serializers for Board model.
"""
from rest_framework import serializers
from kanban_app.models import Board, BoardMembership
from django.contrib.auth import get_user_model
from tasks_app.models import Task

User = get_user_model()


class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing boards.
    
    Provides basic information about boards.
    """
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Board
        fields = ['id', 'title', 'owner', 'owner_name', 'member_count', 'ticket_count']
        read_only_fields = ['id', 'owner', 'owner_name', 'member_count', 'ticket_count']
    
    def get_member_count(self, obj):
        """
        Get the number of board members.
        
        Args:
            obj (Board): The board instance.
            
        Returns:
            int: The number of members.
        """
        return BoardMembership.objects.filter(board=obj).count()
    
    def get_ticket_count(self, obj):
        """
        Get the number of tasks for the board.
        
        Args:
            obj (Board): The board instance.
            
        Returns:
            int: The number of tasks.
        """
        columns = obj.columns.all()
        task_count = Task.objects.filter(column__in=columns).count()
        return task_count


class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating boards.
    
    Handles board creation with members.
    """
    title = serializers.CharField(required=True)
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Board
        fields = ['id', 'title', 'members', 'description']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """
        Create a new board and add members.
        
        Args:
            validated_data (dict): The validated data.
            
        Returns:
            Board: The created board.
        """
        members_data = validated_data.pop('members', [])
        
        if 'title' in validated_data:
            validated_data['name'] = validated_data.pop('title')
            
        board = Board.objects.create(**validated_data)
        
        self._add_members_to_board(board, members_data)
        
        return board
    
    def _add_members_to_board(self, board, member_ids):
        """
        Add members to the board.
        
        Args:
            board (Board): The board to add members to.
            member_ids (list): List of user IDs to add as members.
            
        Returns:
            None
        """
        for user_id in member_ids:
            try:
                user = User.objects.get(id=user_id)
                BoardMembership.objects.create(
                    board=board,
                    user=user,
                    role='MEMBER'
                )
            except User.DoesNotExist:
                pass


class BoardUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating boards.
    
    Handles board updates with members management.
    """
    title = serializers.CharField(required=False)
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Board
        fields = ['title', 'members', 'description']
    
    def update(self, instance, validated_data):
        """
        Update a board with the validated data.
        
        Args:
            instance (Board): The board instance.
            validated_data (dict): The validated data.
            
        Returns:
            Board: The updated board.
        """
        members_data = validated_data.pop('members', None)
        
        if 'title' in validated_data:
            validated_data['name'] = validated_data.pop('title')
            
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        
        if members_data is not None:
            self._update_board_members(instance, members_data)
            
        return instance
    
    def _update_board_members(self, board, member_ids):
        """
        Update the members of a board.
        
        Args:
            board (Board): The board to update members for.
            member_ids (list): List of user IDs to set as members.
            
        Returns:
            None
        """
        BoardMembership.objects.filter(board=board).exclude(
            user=board.owner
        ).delete()
        
        existing_members = set(BoardMembership.objects.filter(
            board=board
        ).values_list('user_id', flat=True))
        
        for user_id in member_ids:
            if user_id not in existing_members:
                try:
                    user = User.objects.get(id=user_id)
                    BoardMembership.objects.create(
                        board=board,
                        user=user,
                        role='MEMBER'
                    )
                except User.DoesNotExist:
                    pass