from rest_framework import serializers
import logging

from ...models import Column

logger = logging.getLogger(__name__)

class ColumnSerializer(serializers.ModelSerializer):
    """
    Serializer for board columns.
    
    Includes associated tasks for complete column representation.
    Board field is read-only to prevent unauthorized modifications.
    """
    tasks = serializers.SerializerMethodField(read_only=True)
    board = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Column
        fields = ['id', 'name', 'position', 'board', 'tasks']
        read_only_fields = ['id', 'board']

    def get_tasks(self, obj):
        try:
            from tasks_app.api.serializers import TaskSerializer
            # Sortiere nach position, dann nach created_at
            tasks = obj.tasks.all().order_by('position', 'created_at')
            return TaskSerializer(tasks, many=True, context=self.context).data
        except Exception as e:
            logger.error(f"Error serializing tasks for column {obj.id}: {str(e)}")
            return []

    def to_representation(self, instance):
        data = super().to_representation(instance)
        logger.info(f"Column {instance.id} '{instance.name}' serialized with {len(data.get('tasks', []))} tasks")
        return data

    def validate_position(self, value):
        if value < 1:
            raise serializers.ValidationError("Position must be positive")
        return value

class ColumnCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new columns."""
    
    class Meta:
        model = Column
        fields = ['name', 'position']
        
    def validate_position(self, value):
        if value < 1:
            raise serializers.ValidationError("Position must be positive")
        return value


class ColumnUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating columns."""
    
    class Meta:
        model = Column
        fields = ['name', 'position']
        
    def validate_position(self, value):
        if value < 1:
            raise serializers.ValidationError("Position must be positive")
        return value