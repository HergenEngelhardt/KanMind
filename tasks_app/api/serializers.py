from rest_framework import serializers
from ..models import Task, Comment
from kanban_app.api.serializers.user_serializers import UserSerializer

class TaskSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    created_by = UserSerializer(read_only=True)
    reviewers = UserSerializer(many=True, read_only=True)
    reviewer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'assignee_id', 'created_by', 'reviewers', 'reviewer_ids',
            'column', 'due_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_ids = validated_data.pop('reviewer_ids', [])
        
        task = Task.objects.create(**validated_data)
        
        if assignee_id:
            from django.contrib.auth.models import User
            try:
                task.assignee = User.objects.get(id=assignee_id)
                task.save()
            except User.DoesNotExist:
                pass
        
        if reviewer_ids:
            from django.contrib.auth.models import User
            reviewers = User.objects.filter(id__in=reviewer_ids)
            task.reviewers.set(reviewers)
        
        return task

    def update(self, instance, validated_data):
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_ids = validated_data.pop('reviewer_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if assignee_id is not None:
            if assignee_id:
                from django.contrib.auth.models import User
                try:
                    instance.assignee = User.objects.get(id=assignee_id)
                except User.DoesNotExist:
                    pass
            else:
                instance.assignee = None
        
        if reviewer_ids is not None:
            from django.contrib.auth.models import User
            reviewers = User.objects.filter(id__in=reviewer_ids)
            instance.reviewers.set(reviewers)
        
        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'task', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)