from rest_framework import serializers
from tasks_app.models import Task, Comment
from django.contrib.auth.models import User
from django.db import models


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for task relationships."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model."""
    
    assignee = UserBasicSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    reviewers = UserBasicSerializer(many=True, read_only=True)
    
    assignee_id = serializers.IntegerField(write_only=True, required=False)
    reviewer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'assignee_id', 'created_by', 
            'reviewers', 'reviewer_ids', 'column',
            'due_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create task with assigned user and reviewers."""
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_ids = validated_data.pop('reviewer_ids', [])
        
        task = Task.objects.create(**validated_data)
        
        if assignee_id:
            try:
                assigned_user = User.objects.get(id=assignee_id)
                task.assignee = assigned_user
                task.save()
            except User.DoesNotExist:
                pass
        
        if reviewer_ids:
            reviewers = User.objects.filter(id__in=reviewer_ids)
            task.reviewers.set(reviewers)
        
        return task

    def update(self, instance, validated_data):
        """Update task with assigned user and reviewers."""
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_ids = validated_data.pop('reviewer_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if assignee_id is not None:
            try:
                if assignee_id:
                    assigned_user = User.objects.get(id=assignee_id)
                    instance.assignee = assigned_user
                else:
                    instance.assignee = None
                instance.save()
            except User.DoesNotExist:
                pass
        
        if reviewer_ids is not None:
            reviewers = User.objects.filter(id__in=reviewer_ids)
            instance.reviewers.set(reviewers)
        
        return instance


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model."""
    
    author = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author', 'task', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def validate_content(self, value):
        """Validate comment content is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty")
        return value.strip()