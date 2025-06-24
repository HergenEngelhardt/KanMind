from rest_framework import serializers
from tasks_app.models import Task, Comment
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "content", "created_at", "updated_at"]
        read_only_fields = ["author", "created_at", "updated_at"]


class TaskSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    assignee = UserSerializer(read_only=True)
    reviewers = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "column",
            "position",
            "assignee",
            "reviewers",
            "comments",
            "created_at",
            "updated_at",
        ]
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.data:
            assignee_id = request.data.get('assignee')
            reviewers_ids = request.data.get('reviewers')
            
            instance.title = validated_data.get('title', instance.title)
            instance.description = validated_data.get('description', instance.description)
            instance.position = validated_data.get('position', instance.position)
            
            if 'column' in validated_data:
                instance.column = validated_data.get('column')
            
            if assignee_id:
                try:
                    user = User.objects.get(id=assignee_id)
                    instance.assignee = user
                except User.DoesNotExist:
                    pass
            elif 'assignee' in request.data and assignee_id is None:
                instance.assignee = None
            
            instance.save()
            
            if reviewers_ids is not None:
                instance.reviewers.clear()
                
                if reviewers_ids:
                    for reviewer_id in reviewers_ids:
                        try:
                            reviewer = User.objects.get(id=reviewer_id)
                            instance.reviewers.add(reviewer)
                        except User.DoesNotExist:
                            continue
        
        return instance