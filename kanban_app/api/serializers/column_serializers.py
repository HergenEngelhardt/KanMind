from rest_framework import serializers
from kanban_app.models import Column


class ColumnSerializer(serializers.ModelSerializer):
    """
    Serializer for board columns.
    
    Includes associated tasks for complete column representation.
    Board field is read-only to prevent unauthorized modifications.
    """
    def get_tasks_serializer(self):
        from tasks_app.api.serializers import TaskSerializer
        return TaskSerializer
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        TaskSerializer = self.get_tasks_serializer()
        if hasattr(instance, 'tasks'):
            data['tasks'] = TaskSerializer(instance.tasks.all().order_by('position'), many=True).data
        else:
            data['tasks'] = []
        return data
    
    class Meta:
        model = Column
        fields = ["id", "name", "position", "board"]
        read_only_fields = ["board"]

    def validate_position(self, value):
        """
        Validate column position is positive.
        
        Args:
            value (int): Position value
            
        Returns:
            int: Validated position
            
        Raises:
            ValidationError: If position is not positive
        """
        if value < 1:
            raise serializers.ValidationError(
                "Position must be a positive integer."
            )
        return value