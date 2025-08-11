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
    
    Args:
        serializers.ModelSerializer: Base serializer class
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
    
    Args:
        serializers.ModelSerializer: Base serializer class
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ('id', 'task', 'user', 'content', 'created_at')
        read_only_fields = ('task', 'user', 'created_at')


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for tasks.
    
    Handles serialization and deserialization of Task model instances.
    
    Args:
        serializers.ModelSerializer: Base serializer class
    """
    assigned_to = UserSerializer(read_only=True)
    reviewers = UserSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = ('id', 'column', 'title', 'description', 'assigned_to', 
                  'reviewers', 'created_by', 'created_at', 'updated_at', 
                  'priority', 'status', 'due_date', 'position')
        read_only_fields = ('created_by', 'created_at', 'updated_at')