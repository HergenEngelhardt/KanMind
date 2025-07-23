from rest_framework import serializers
from django.core.cache import cache
import logging

from kanban_app.models import Column

logger = logging.getLogger(__name__)


class ColumnSerializer(serializers.ModelSerializer):
    tasks = serializers.SerializerMethodField(read_only=True)
    board = serializers.PrimaryKeyRelatedField(read_only=True)
    title = serializers.CharField(source='title', read_only=True)

    class Meta:
        model = Column
        fields = ['id', 'title', 'order', 'created_at', 'updated_at', 'position', 'board', 'tasks']
        read_only_fields = ['id', 'board']

    def get_tasks(self, obj):
        cache_key = f"column_tasks_{obj.id}_{obj.updated_at.timestamp()}"
        cached_tasks = cache.get(cache_key)
        
        if cached_tasks:
            return cached_tasks
            
        try:
            from tasks_app.api.serializers import TaskSerializer
            tasks = obj.tasks.all().select_related(
                'assignee', 'created_by'
            ).prefetch_related('reviewers').order_by('position', 'created_at')
            
            tasks_data = TaskSerializer(tasks, many=True, context=self.context).data
            
            cache.set(cache_key, tasks_data, 300)
            return tasks_data
            
        except Exception as e:
            logger.error(f"Error serializing tasks for column {obj.id}: {str(e)}")
            return []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        if len(data.get('tasks', [])) == 0 and instance.tasks.exists():
            logger.warning(f"Column {instance.id} has tasks but serialization returned empty list")
        
        return data

    def validate_position(self, value):
        if value < 1:
            raise serializers.ValidationError("Position must be positive")
        return value


class ColumnCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ['title', 'position']
        
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Column title cannot be empty")
        return value.strip()
        
    def validate_position(self, value):
        if value < 1:
            raise serializers.ValidationError("Position must be positive")
        return value


class ColumnUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ['title', 'position']
        
    def validate_title(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Column title cannot be empty")
        return value.strip() if value else value
        
    def validate_position(self, value):
        if value < 1:
            raise serializers.ValidationError("Position must be positive")
        return value

    def update(self, instance, validated_data):
        cache.delete(f"column_tasks_{instance.id}_*")
        if instance.board:
            cache.delete(f"board_columns_{instance.board.id}_*")
            cache.delete(f"board_tasks_{instance.board.id}_*")
            
        return super().update(instance, validated_data)


class ColumnSimpleSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='title', read_only=True)
    
    class Meta:
        model = Column
        fields = ['id', 'title', 'name', 'position']
        read_only_fields = ['id']
        
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Column title cannot be empty")
        return value.strip()