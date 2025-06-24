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
