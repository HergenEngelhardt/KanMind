"""
Serializers for tasks API.

This module contains serializers for Task and Comment models.
"""
from rest_framework import serializers
from tasks_app.models import Task, Comment
from django.contrib.auth import get_user_model
from kanban_app.models import Board, Column

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user information within tasks.
    
    Provides basic user information for assignee and reviewer fields.
    """
    fullname = serializers.CharField(source='get_full_name')
    
    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model.
    
    Used for list views and creation of tasks.
    """
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all(),
        write_only=True,
        required=False
    )
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
        source='assignee'
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
        source='reviewer'
    )
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'board', 'column', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'assignee_id', 'reviewer_id',
            'due_date', 'comments_count'
        ]
        read_only_fields = ['id', 'column']
    
    def get_comments_count(self, obj):
        """
        Get the number of comments for the task.
        
        Args:
            obj (Task): The Task instance.
            
        Returns:
            int: The number of comments.
        """
        return obj.comments.count()
    
    def validate_status(self, value):
        """
        Validate the status field.
        
        Args:
            value (str): The status value to validate.
            
        Returns:
            str: The validated status.
            
        Raises:
            ValidationError: If status is not one of the allowed values.
        """
        valid_statuses = ['to-do', 'in-progress', 'review', 'done']
        if value and value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return value
    
    def validate_priority(self, value):
        """
        Validate the priority field.
        
        Args:
            value (str): The priority value to validate.
            
        Returns:
            str: The validated priority.
            
        Raises:
            ValidationError: If priority is not one of the allowed values.
        """
        valid_priorities = ['low', 'medium', 'high']
        if value and value not in valid_priorities:
            raise serializers.ValidationError(
                f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
            )
        return value
    
    def validate_column(self, value):
        """
        Validate that the column isn't changed to a different board during updates.
        
        Args:
            value: The column value from the request.
            
        Returns:
            Column: The validated column.
            
        Raises:
            ValidationError: If attempting to change to a column from a different board.
        """
        if self.instance and self.instance.column.board.id != value.board.id:
            raise serializers.ValidationError(
                "Cannot change task to a column from a different board"
            )
        return value


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model.
    
    Used for listing and creating comments.
    """
    author = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
        read_only_fields = ['created_at', 'author']