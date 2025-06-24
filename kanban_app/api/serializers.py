from tasks_app.api.serializers import TaskSerializer, UserSerializer
from rest_framework import serializers
from kanban_app.models import Board, BoardMembership, Column
from django.contrib.auth.models import User


class BoardListSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Board
        fields = ["id", "name", "description", "owner", "created_at", "updated_at"]


class BoardMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = BoardMembership
        fields = ["id", "user", "role"]


class ColumnSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Column
        fields = ["id", "name", "position", "board", "tasks"]
        read_only_fields = ["board"]


class BoardDetailSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = BoardMembershipSerializer(
        source="boardmembership_set", many=True, read_only=True
    )
    columns = ColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "members",
            "columns",
            "created_at",
            "updated_at",
        ]
