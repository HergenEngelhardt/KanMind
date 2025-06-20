from rest_framework import serializers
from django.contrib.auth.models import User
from tasks_app.models import Task

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'column', 'position', 
                  'created_by', 'assigned_to', 'created_at', 'updated_at']

class TaskSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'column', 'position', 
                  'created_by', 'assigned_to', 'created_at', 'updated_at']