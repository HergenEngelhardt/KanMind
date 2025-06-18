from rest_framework import serializers
from tasks_app.models import Task
from kanban_app.api.serializers import UserSerializer

class TaskSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'column', 'position', 
                  'created_by', 'assigned_to', 'created_at', 'updated_at']