"""
Serializers for tasks and comments in the tasks_app.

Provides serialization and deserialization for Task and Comment models.
"""
from rest_framework import serializers
from tasks_app.models import Task, Comment  
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user representation within tasks.
    """
    fullname = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'fullname')
    
    def get_fullname(self, obj):
        """
        Compute the full name of the user.
        
        Args:
            obj (User): User object to get name from
            
        Returns:
            str: Full name or username if no name is set
        """
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name or obj.username


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments.
    
    Handles serialization and deserialization of Comment model instances.
    """
    user = UserSerializer(read_only=True, source='created_by')
    
    class Meta:
        model = Comment
        fields = ('id', 'task', 'user', 'content', 'created_at')
        read_only_fields = ('task', 'created_at')


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for tasks.
    
    Handles serialization and deserialization of Task model instances.
    """
    assigned_to = UserSerializer(read_only=True, source='assignee')
    reviewers = UserSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = (
            'id', 'column', 'title', 'description', 'assigned_to',
            'reviewers', 'created_by', 'created_at', 'updated_at',
            'priority', 'status', 'due_date'
        )
        read_only_fields = ('created_by', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """
        Create a new task instance.
        
        Args:
            validated_data (dict): Validated data for task creation
            
        Returns:
            Task: Created task instance
            
        Raises:
            ValidationError: If data is invalid
        """
        return self._process_task_data(validated_data, is_new=True)
    
    def update(self, instance, validated_data):
        """
        Update an existing task instance.
        
        Args:
            instance (Task): Task instance to update
            validated_data (dict): Validated data for update
            
        Returns:
            Task: Updated task instance
            
        Raises:
            ValidationError: If data is invalid
        """
        return self._process_task_data(validated_data, instance=instance)
    
    def _process_task_data(self, validated_data, instance=None, is_new=False):
        """
        Process task data for create or update operations.
        
        Args:
            validated_data (dict): Validated task data
            instance (Task, optional): Existing task for update. Defaults to None.
            is_new (bool, optional): Whether this is a new task. Defaults to False.
            
        Returns:
            Task: Created or updated task instance
        """
        assignee_id = self.initial_data.get('assigned_to')
        
        if assignee_id:
            validated_data['assignee_id'] = assignee_id
        
        if is_new:
            return super().create(validated_data)
        return super().update(instance, validated_data)