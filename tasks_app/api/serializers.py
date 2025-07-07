from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import Task, Comment  


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model in task context.
    """
    
    fullname = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'fullname']
        read_only_fields = ['id', 'username', 'email', 'first_name', 'last_name']
    
    def get_fullname(self, obj):
        """Get user's full name."""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model.
    """
    author = UserSerializer(read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_email = serializers.CharField(source='author.email', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'author_name', 'author_email', 'task', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'task', 'created_at', 'updated_at']
    
    def validate_content(self, value):
        """Validate comment content."""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty.")
        return value.strip()


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model.
    
    Handles task creation and updates with proper validation.
    Includes nested serializers for related objects.
    """
    
    assignee = UserSerializer(read_only=True)
    reviewers = UserSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'column', 'position',
            'assignee', 'assignee_id', 'reviewers', 'reviewer_ids',
            'comments', 'created_at', 'updated_at', 'status'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_title(self, value):
        """Validate task title."""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("Task title cannot be empty.")
        if len(value.strip()) > 200:
            raise serializers.ValidationError("Task title cannot exceed 200 characters.")
        return value.strip()

    def validate_position(self, value):
        """Validate task position."""
        if value < 0:
            raise serializers.ValidationError("Position cannot be negative.")
        return value

    def validate_assignee_id(self, value):
        """Validate assignee ID."""
        if value is not None and not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid assignee ID.")
        return value

    def validate_reviewer_ids(self, value):
        """Validate reviewer IDs."""
        if value:
            existing_ids = set(User.objects.filter(id__in=value).values_list('id', flat=True))
            if len(existing_ids) != len(value):
                raise serializers.ValidationError("One or more reviewer IDs are invalid.")
        return value

    def create(self, validated_data):
        """
        Create task with assignee and reviewers.
        """
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_ids = validated_data.pop('reviewer_ids', [])
        
        task = Task.objects.create(**validated_data)
        
        if assignee_id:
            task.assignee_id = assignee_id
            task.save()
        
        if reviewer_ids:
            task.reviewers.set(reviewer_ids)
        
        return task

    def update(self, instance, validated_data):
        """
        Update task instance with validated data.
        """
        request = self.context.get('request')
        if not request or not request.data:
            return super().update(instance, validated_data)
        
        self._update_basic_fields(instance, validated_data)
        self._update_assignee(instance, request.data.get('assignee_id'))
        self._update_reviewers(instance, request.data.get('reviewer_ids'))
        
        instance.save()
        return instance

    def _update_basic_fields(self, instance, validated_data):
        """Update basic task fields."""
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.position = validated_data.get('position', instance.position)
        
        if 'column' in validated_data:
            instance.column = validated_data.get('column')

    def _update_assignee(self, instance, assignee_id):
        """Update task assignee."""
        if assignee_id is not None:
            if assignee_id == '':
                instance.assignee = None
            else:
                try:
                    assignee = User.objects.get(id=int(assignee_id))
                    instance.assignee = assignee
                except (User.DoesNotExist, ValueError):
                    pass

    def _update_reviewers(self, instance, reviewer_ids):
        """Update task reviewers."""
        if reviewer_ids is not None:
            if not reviewer_ids:
                instance.reviewers.clear()
            else:
                try:
                    valid_ids = [int(rid) for rid in reviewer_ids if str(rid).isdigit()]
                    if valid_ids:
                        existing_users = User.objects.filter(id__in=valid_ids)
                        instance.reviewers.set(existing_users)
                except (ValueError, TypeError):
                    pass