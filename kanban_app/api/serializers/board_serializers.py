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
    
    Provides information about boards according to API spec.
    """
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Board
        fields = ['id', 'title', 'member_count', 'ticket_count', 
                  'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id']
        read_only_fields = ['id', 'owner_id', 'member_count', 'ticket_count',
                           'tasks_to_do_count', 'tasks_high_prio_count']
    
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
    
    def get_tasks_to_do_count(self, obj):
        """
        Get the number of tasks in 'to-do' status.
        
        Args:
            obj (Board): The board instance.
            
        Returns:
            int: The number of 'to-do' tasks.
        """
        columns = obj.columns.all()
        return Task.objects.filter(column__in=columns, status='to-do').count()
    
    def get_tasks_high_prio_count(self, obj):
        """
        Get the number of tasks with 'high' priority.
        
        Args:
            obj (Board): The board instance.
            
        Returns:
            int: The number of high priority tasks.
        """
        columns = obj.columns.all()
        return Task.objects.filter(column__in=columns, priority='high').count()


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
        """
        self._remove_existing_members(board)
        existing_members = self._get_existing_member_ids(board)
        self._add_new_members(board, member_ids, existing_members)
    
    def _remove_existing_members(self, board):
        """
        Remove existing board members except owner.
        
        Args:
            board (Board): The board to remove members from.
        """
        BoardMembership.objects.filter(board=board).exclude(
            user=board.owner
        ).delete()
    
    def _get_existing_member_ids(self, board):
        """
        Get IDs of existing board members.
        
        Args:
            board (Board): The board to get member IDs for.
            
        Returns:
            set: Set of user IDs.
        """
        return set(BoardMembership.objects.filter(
            board=board
        ).values_list('user_id', flat=True))
    
    def _add_new_members(self, board, member_ids, existing_members):
        """
        Add new members to the board.
        
        Args:
            board (Board): The board to add members to.
            member_ids (list): List of user IDs to add.
            existing_members (set): Set of existing member IDs.
        """
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