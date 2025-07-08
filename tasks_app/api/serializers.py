from rest_framework import serializers
from django.contrib.auth.models import User
from tasks_app.models import Task, Comment


class UserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "fullname"]
        read_only_fields = ["id"]

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class TaskSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    reviewers = UserSerializer(many=True, read_only=True)
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "column", "position", 
            "assignee", "assignee_id", "reviewers", "reviewer_ids",
            "due_date", "priority", "status", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_ids = validated_data.pop('reviewer_ids', [])
        
        task = Task.objects.create(**validated_data)
        
        if assignee_id:
            try:
                assignee = User.objects.get(id=assignee_id)
                task.assignee = assignee
                task.save()
            except User.DoesNotExist:
                pass
        
        if reviewer_ids:
            reviewers = User.objects.filter(id__in=reviewer_ids)
            task.reviewers.set(reviewers)
        
        return task

    def update(self, instance, validated_data):
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_ids = validated_data.pop('reviewer_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if assignee_id is not None:
            if assignee_id:
                try:
                    assignee = User.objects.get(id=assignee_id)
                    instance.assignee = assignee
                except User.DoesNotExist:
                    instance.assignee = None
            else:
                instance.assignee = None
            instance.save()
        
        if reviewer_ids is not None:
            reviewers = User.objects.filter(id__in=reviewer_ids)
            instance.reviewers.set(reviewers)
        
        return instance


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "task", "author", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "author", "created_at", "updated_at"]