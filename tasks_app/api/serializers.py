"""
Serializers for tasks and comments in the tasks_app.

Provides serialization and deserialization for Task and Comment models.
"""
from rest_framework import serializers
from tasks_app.models import Task, Comment  
from django.contrib.auth.models import User
from kanban_app.models import Column
import logging

logger = logging.getLogger(__name__)


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
            'id', 'column', 'title', 'description', 'assigned_to', 'assignee',
            'reviewers', 'created_by', 'created_at', 'updated_at',
            'priority', 'status', 'due_date'
        )
        read_only_fields = ('created_by', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        """
        Validate task data as a whole.
        
        Args:
            attrs (dict): The attribute dictionary to validate
            
        Returns:
            dict: The validated attributes
            
        Raises:
            ValidationError: If validation fails
        """
        self.validate_required_fields(attrs)
        self.validate_column_field(attrs)
        self.validate_priority_field(attrs)
        self.validate_status_field(attrs)
        
        return attrs
    
    def validate_required_fields(self, attrs):
        """
        Validate required fields are present.
        
        Args:
            attrs (dict): Attributes to validate
            
        Raises:
            ValidationError: If required fields missing
        """
        errors = {}
        
        if 'title' not in attrs:
            errors['title'] = "Title field is required"
            
        if 'column' not in attrs:
            errors['column'] = "Column field is required"
            
        if errors:
            raise serializers.ValidationError(errors)
    
    def validate_column_field(self, attrs):
        """
        Validate column field exists and is valid.
        
        Args:
            attrs (dict): Attribute dictionary to validate
            
        Raises:
            ValidationError: If column is invalid
        """
        if 'column' not in attrs:
            return
            
        column_data = attrs['column']
        
        try:
            if isinstance(column_data, Column):
                return
            
            column_id = int(column_data)
            attrs['column'] = Column.objects.get(id=column_id)
        except (ValueError, TypeError):
            raise serializers.ValidationError({
                'column': 'Column ID must be a number'
            })
        except Column.DoesNotExist:
            raise serializers.ValidationError({
                'column': f'Column with id {column_data} does not exist'
            })
    
    def validate_priority_field(self, attrs):
        """
        Validate priority field if present.
        
        Args:
            attrs (dict): Attribute dictionary to validate
            
        Raises:
            ValidationError: If priority is invalid
        """
        if 'priority' not in attrs:
            return
            
        valid_priorities = ['low', 'medium', 'high']
        if attrs['priority'] not in valid_priorities:
            raise serializers.ValidationError({
                'priority': f'Priority must be one of: {", ".join(valid_priorities)}'
            })
    
    def validate_status_field(self, attrs):
        """
        Validate status field if present.
        
        Args:
            attrs (dict): Attribute dictionary to validate
            
        Raises:
            ValidationError: If status is invalid
        """
        if 'status' not in attrs:
            return
            
        valid_statuses = ['to-do', 'in-progress', 'review', 'done']
        if attrs['status'] not in valid_statuses:
            raise serializers.ValidationError({
                'status': f'Status must be one of: {", ".join(valid_statuses)}'
            })
    
    def create(self, validated_data):
        """
        Create a new task instance.
        
        Args:
            validated_data (dict): Validated data for task creation
            
        Returns:
            Task: Created task instance
        """
        reviewers_data = self.initial_data.get('reviewers', [])
        assignee_id = self.initial_data.get('assignee')
        
        task = Task.objects.create(**validated_data)
        
        self.process_assignee(task, assignee_id)
        self.process_reviewers(task, reviewers_data)
        
        return task
    
    def update(self, instance, validated_data):
        """
        Update an existing task instance.
        
        Args:
            instance (Task): Task instance to update
            validated_data (dict): Validated data for update
            
        Returns:
            Task: Updated task instance
        """
        reviewers_data = self.initial_data.get('reviewers', [])
        assignee_id = self.initial_data.get('assignee')
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        self.process_assignee(instance, assignee_id)
        self.process_reviewers(instance, reviewers_data)
        
        return instance
    
    def process_assignee(self, task, assignee_id):
        """
        Process assignee field.
        
        Args:
            task (Task): Task to update
            assignee_id: ID of assignee user
        """
        if not assignee_id:
            return
            
        try:
            assignee_id = int(assignee_id)
            user = User.objects.get(id=assignee_id)
            task.assignee = user
            task.save()
        except (ValueError, TypeError, User.DoesNotExist):
            pass
    
    def process_reviewers(self, task, reviewer_ids):
        """
        Process reviewers field.
        
        Args:
            task (Task): Task to update
            reviewer_ids: List of reviewer user IDs
        """
        if not reviewer_ids or not isinstance(reviewer_ids, list):
            return
            
        task.reviewers.clear()
        
        for reviewer_id in reviewer_ids:
            try:
                reviewer_id = int(reviewer_id)
                user = User.objects.get(id=reviewer_id)
                task.reviewers.add(user)
            except (ValueError, TypeError, User.DoesNotExist):
                continue