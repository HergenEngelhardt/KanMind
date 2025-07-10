from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.cache import cache
import logging

from tasks_app.models import Task, Comment

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """Optimierter User Serializer mit Caching."""
    
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'fullname', 'username']

    def get_fullname(self, obj):
        """Cached fullname generation."""
        cache_key = f"user_fullname_{obj.id}"
        cached_fullname = cache.get(cache_key)
        
        if cached_fullname:
            return cached_fullname
            
        fullname = f"{obj.first_name} {obj.last_name}".strip() or obj.username
        
        cache.set(cache_key, fullname, 3600)
        return fullname


class CommentSerializer(serializers.ModelSerializer):
    """Optimierter Comment Serializer."""
    
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at']

    def get_author(self, obj):
        """Cached author information."""
        cache_key = f"user_info_{obj.author.id}"
        cached_author = cache.get(cache_key)
        
        if cached_author:
            return cached_author
            
        author_data = f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.username
        
        cache.set(cache_key, author_data, 1800)
        return author_data

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty")
        return value.strip()


class TaskSerializer(serializers.ModelSerializer):
    """Optimierter Task Serializer mit Caching."""
    
    assignee = UserSerializer(read_only=True)
    reviewer = serializers.SerializerMethodField()
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    comments_count = serializers.SerializerMethodField()
    board = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'assignee_id', 'reviewer_id',
            'due_date', 'comments_count', 'board', 'created_at', 'updated_at'
        ]

    def get_reviewer(self, obj):
        """Cached reviewer information."""
        if not obj.reviewers.exists():
            return None
            
        reviewer = obj.reviewers.first()
        cache_key = f"user_info_detailed_{reviewer.id}"
        cached_reviewer = cache.get(cache_key)
        
        if cached_reviewer:
            return cached_reviewer
            
        reviewer_data = {
            'id': reviewer.id,
            'fullname': f"{reviewer.first_name} {reviewer.last_name}".strip() or reviewer.username,
            'email': reviewer.email,
            'username': reviewer.username
        }
        
        cache.set(cache_key, reviewer_data, 1800)
        return reviewer_data

    def get_comments_count(self, obj):
        """Cached comments count."""
        cache_key = f"task_comments_count_{obj.id}"
        cached_count = cache.get(cache_key)
        
        if cached_count is not None:
            return cached_count
            
        count = obj.comments.count()
        
        cache.set(cache_key, count, 300)
        return count

    def create(self, validated_data):
        """Optimierte Task-Erstellung."""
        board_id = validated_data.pop('board', None)
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        
        if board_id:
            from kanban_app.models import Board
            try:
                board = Board.objects.get(id=board_id)
                column = board.columns.first()
                if not column:
                    from kanban_app.models import Column
                    column = Column.objects.create(
                        name='To Do',
                        board=board,
                        position=0
                    )
            except Board.DoesNotExist:
                raise serializers.ValidationError("Board not found")
        else:
            raise serializers.ValidationError("Board ID is required")
        
        task = Task.objects.create(
            column=column,
            assignee_id=assignee_id,
            created_by=self.context['request'].user,
            **validated_data
        )
        
        if reviewer_id:
            try:
                reviewer = User.objects.get(id=reviewer_id)
                task.reviewers.add(reviewer)
            except User.DoesNotExist:
                pass
        
        cache.delete(f"board_tasks_{board_id}_*")
        cache.delete(f"task_comments_count_{task.id}")
        
        return task

    def update(self, instance, validated_data):
        """Optimierte Task-Update."""
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        validated_data.pop('board', None)  
        
        if assignee_id is not None:
            instance.assignee_id = assignee_id
        
        if reviewer_id is not None:
            instance.reviewers.clear()
            if reviewer_id:
                try:
                    reviewer = User.objects.get(id=reviewer_id)
                    instance.reviewers.add(reviewer)
                except User.DoesNotExist:
                    pass
        
        cache.delete(f"task_comments_count_{instance.id}")
        if instance.column and instance.column.board:
            cache.delete(f"board_tasks_{instance.column.board.id}_*")
            
        return super().update(instance, validated_data)