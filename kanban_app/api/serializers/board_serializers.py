from rest_framework import serializers
from kanban_app.models import Board, BoardMembership
from django.contrib.auth import get_user_model
from tasks_app.models import Task

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user data in board responses.
    
    This serializer returns basic user information for board members.
    """
    fullname = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']
        
    def get_fullname(self, obj):
        """
        Format user's full name.
        
        Args:
            obj (User): User instance
            
        Returns:
            str: User's full name
        """
        return f"{obj.first_name} {obj.last_name}".strip()

class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for board list representation.
    """
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.SerializerMethodField()
    title = serializers.CharField(source='name')
    
    class Meta:
        model = Board
        fields = ['id', 'title', 'member_count', 'ticket_count', 'tasks_to_do_count', 
                 'tasks_high_prio_count', 'owner_id']
    
    def get_member_count(self, obj):
        """
        Returns count of board members.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            int: Number of members
        """
        return obj.members.count()
    
    def get_ticket_count(self, obj):
        """
        Returns count of tasks in board.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            int: Number of tasks
        """
        return Task.objects.filter(board=obj).count()
    
    def get_tasks_to_do_count(self, obj):
        """
        Returns count of to-do tasks in board.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            int: Number of to-do tasks
        """
        return Task.objects.filter(board=obj, status='to-do').count()
    
    def get_tasks_high_prio_count(self, obj):
        """
        Returns count of high priority tasks in board.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            int: Number of high priority tasks
        """
        return Task.objects.filter(board=obj, priority='high').count()
    
    def get_owner_id(self, obj):
        """
        Returns owner's ID.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            int: Owner's user ID
        """
        return obj.owner.id

class BoardUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a board.
    
    This serializer handles board updates and returns the correct format.
    """
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False
    )
    owner_data = serializers.SerializerMethodField()
    members_data = serializers.SerializerMethodField()
    title = serializers.CharField(source='name')
    
    class Meta:
        model = Board
        fields = ['id', 'title', 'members', 'owner_data', 'members_data']
    
    def get_owner_data(self, obj):
        """
        Return serialized owner information.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            dict: Owner data
        """
        return UserSerializer(obj.owner).data
    
    def get_members_data(self, obj):
        """
        Return serialized members information.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            list: List of member data dictionaries
        """
        return UserSerializer(obj.members.all(), many=True).data
    
    def update(self, instance, validated_data):
        """
        Update the board instance with validated data.
        
        Args:
            instance (Board): Board instance to update
            validated_data (dict): Validated data
            
        Returns:
            Board: Updated board instance
        """
        members = validated_data.pop('members', None)
        
        if 'name' in validated_data:
            instance.name = validated_data.pop('name')
            instance.save()
        
        if members is not None:
            self._update_members(instance, members)
        
        return instance
    
    def _update_members(self, board, members):
        """
        Update board members.
        
        Args:
            board (Board): Board instance
            members (list): List of User objects
        """
        BoardMembership.objects.filter(board=board).exclude(
            user=board.owner
        ).delete()
        
        for member in members:
            if member != board.owner:
                BoardMembership.objects.get_or_create(
                    board=board, 
                    user=member,
                    defaults={'role': 'MEMBER'}
                )