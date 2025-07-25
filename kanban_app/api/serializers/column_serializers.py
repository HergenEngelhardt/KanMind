from rest_framework import serializers
from django.core.cache import cache
import logging

from kanban_app.models import Column

logger = logging.getLogger(__name__)


class ColumnSerializer(serializers.ModelSerializer):
    """
    Serializer for Column model with tasks and caching support.
    
    Provides full column data including associated tasks with caching
    for performance optimization.
    """
    
    tasks = serializers.SerializerMethodField(read_only=True)
    board = serializers.PrimaryKeyRelatedField(read_only=True)
    title = serializers.CharField(source='title', read_only=True)

    class Meta:
        model = Column
        fields = ['id', 'title', 'order', 'created_at', 'updated_at', 'position', 'board', 'tasks']
        read_only_fields = ['id', 'board']

    def get_tasks(self, obj):
        """
        Get tasks for a column with caching.
        
        Args:
            obj (Column): Column instance
            
        Returns:
            list: Serialized task data
        """
        cache_key = f"column_tasks_{obj.id}_{obj.updated_at.timestamp()}"
        cached_tasks = cache.get(cache_key)
        
        if cached_tasks:
            return cached_tasks
            
        return self._serialize_tasks(obj, cache_key)

    def _serialize_tasks(self, obj, cache_key):
        """
        Serialize tasks for a column and cache the result.
        
        Args:
            obj (Column): Column instance
            cache_key (str): Cache key for storing results
            
        Returns:
            list: Serialized task data
        """
        try:
            from tasks_app.api.serializers import TaskSerializer
            tasks = self._get_optimized_tasks(obj)
            tasks_data = TaskSerializer(tasks, many=True, context=self.context).data
            cache.set(cache_key, tasks_data, 300)
            return tasks_data
        except Exception as e:
            logger.error(f"Error serializing tasks for column {obj.id}: {str(e)}")
            return []

    def _get_optimized_tasks(self, obj):
        """
        Get tasks with optimized database queries.
        
        Args:
            obj (Column): Column instance
            
        Returns:
            QuerySet: Optimized task queryset
        """
        return obj.tasks.all().select_related(
            'assignee', 'created_by'
        ).prefetch_related('reviewers').order_by('position', 'created_at')

    def to_representation(self, instance):
        """
        Convert instance to dictionary representation.
        
        Args:
            instance (Column): Column instance to serialize
            
        Returns:
            dict: Serialized column data
        """
        data = super().to_representation(instance)
        
        if len(data.get('tasks', [])) == 0 and instance.tasks.exists():
            logger.warning(f"Column {instance.id} has tasks but serialization returned empty list")
        
        return data

    def validate_position(self, value):
        """
        Validate position field.
        
        Args:
            value (int): Position value to validate
            
        Returns:
            int: Validated position value
            
        Raises:
            ValidationError: If position is not positive
        """
        if value < 1:
            raise serializers.ValidationError("Position must be positive")
        return value


class ColumnCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new Column instances.
    
    Handles validation and creation of new columns with required fields.
    """
    
    class Meta:
        model = Column
        fields = ['title', 'position']
        
    def validate_title(self, value):
        """
        Validate title field.
        
        Args:
            value (str): Title value to validate
            
        Returns:
            str: Validated and stripped title
            
        Raises:
            ValidationError: If title is empty or whitespace only
        """
        if not value.strip():
            raise serializers.ValidationError("Column title cannot be empty")
        return value.strip()
        
    def validate_position(self, value):
        """
        Validate position field.
        
        Args:
            value (int): Position value to validate
            
        Returns:
            int: Validated position value
            
        Raises:
            ValidationError: If position is not positive
        """
        if value < 1:
            raise serializers.ValidationError("Position must be positive")
        return value


class ColumnUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing Column instances.
    
    Handles partial updates and cache invalidation for modified columns.
    """
    
    class Meta:
        model = Column
        fields = ['title', 'position']
        
    def validate_title(self, value):
        """
        Validate title field for updates.
        
        Args:
            value (str): Title value to validate
            
        Returns:
            str: Validated and stripped title or original value
            
        Raises:
            ValidationError: If title is provided but empty/whitespace only
        """
        if value and not value.strip():
            raise serializers.ValidationError("Column title cannot be empty")
        return value.strip() if value else value
        
    def validate_position(self, value):
        """
        Validate position field.
        
        Args:
            value (int): Position value to validate
            
        Returns:
            int: Validated position value
            
        Raises:
            ValidationError: If position is not positive
        """
        if value < 1:
            raise serializers.ValidationError("Position must be positive")
        return value

    def update(self, instance, validated_data):
        """
        Update column instance and invalidate related caches.
        
        Args:
            instance (Column): Column instance to update
            validated_data (dict): Validated data for update
            
        Returns:
            Column: Updated column instance
        """
        self._invalidate_caches(instance)
        return super().update(instance, validated_data)

    def _invalidate_caches(self, instance):
        """
        Invalidate related caches for the column.
        
        Args:
            instance (Column): Column instance whose caches to invalidate
        """
        cache.delete(f"column_tasks_{instance.id}_*")
        if instance.board:
            cache.delete(f"board_columns_{instance.board.id}_*")
            cache.delete(f"board_tasks_{instance.board.id}_*")


class ColumnSimpleSerializer(serializers.ModelSerializer):
    """
    Simple serializer for Column model with minimal fields.
    
    Used for lightweight column representations without tasks or detailed info.
    """
    
    title = serializers.CharField(source='title', read_only=True)
    
    class Meta:
        model = Column
        fields = ['id', 'title', 'name', 'position']
        read_only_fields = ['id']
        
    def validate_title(self, value):
        """
        Validate title field.
        
        Args:
            value (str): Title value to validate
            
        Returns:
            str: Validated and stripped title
            
        Raises:
            ValidationError: If title is empty or whitespace only
        """
        if not value.strip():
            raise serializers.ValidationError("Column title cannot be empty")
        return value.strip()