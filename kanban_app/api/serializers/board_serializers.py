from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.cache import cache
import logging

from kanban_app.models import Board, BoardMembership
from auth_app.api.serializers import UserSerializer


class BoardListSerializer(serializers.ModelSerializer):
    """Optimierter Serializer für Board-Listen mit weniger Daten."""
    
    owner = UserSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    ticket_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Board
        fields = [
            'id', 'title', 'description', 'status', 'owner', 
            'member_count', 'ticket_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class BoardCreateSerializer(serializers.ModelSerializer):
    """Serializer für Board-Erstellung."""
    
    members = serializers.ListField(
        child=serializers.IntegerField(), 
        required=False, 
        allow_empty=True
    )
    
    class Meta:
        model = Board
        fields = ['title', 'description', 'members']
        
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Board title cannot be empty")
        return value.strip()
        
    def validate_members(self, value):
        if value:
            existing_users = User.objects.filter(id__in=value).count()
            if existing_users != len(value):
                raise serializers.ValidationError("Some user IDs do not exist")
        return value


class BoardDetailSerializer(serializers.ModelSerializer):
    """Optimierter Serializer für Board-Details mit Caching."""

    owner = UserSerializer(read_only=True)
    members = serializers.SerializerMethodField()
    columns = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    title = serializers.CharField(source='name', required=True)
    deadline = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = Board
        fields = [
            'id', 'title', 'description', 'status', 'owner', 'members',
            'columns', 'tasks', 'deadline', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_members(self, obj):
        """Optimierte Member-Serialisierung mit Caching."""
        cache_key = f"board_members_{obj.id}_{obj.updated_at.timestamp()}"
        cached_members = cache.get(cache_key)

        if cached_members:
            return cached_members

        try:
            memberships = BoardMembership.objects.filter(board=obj).select_related('user')
            members_data = [
                {
                    'id': membership.user.id,
                    'fullname': f"{membership.user.first_name} {membership.user.last_name}".strip() or membership.user.username,
                    'email': membership.user.email,
                    'role': membership.role
                }
                for membership in memberships
            ]

            cache.set(cache_key, members_data, 600)
            return members_data

        except Exception as e:
            return []

    def get_columns(self, obj):
        """Optimierte Column-Serialisierung mit Caching."""
        cache_key = f"board_columns_{obj.id}_{obj.updated_at.timestamp()}"
        cached_columns = cache.get(cache_key)

        if cached_columns:
            return cached_columns

        try:
            columns = obj.columns.all().order_by('position')
            columns_data = [
                {
                    'id': column.id,
                    'title': column.title,  
                    'name': column.title,   
                    'position': column.position
                }
                for column in columns
            ]

            cache.set(cache_key, columns_data, 600)
            return columns_data

        except Exception as e:
            return []

    def get_tasks(self, obj):
        """Optimierte Task-Serialisierung mit Caching."""
        cache_key = f"board_tasks_{obj.id}_{obj.updated_at.timestamp()}"
        cached_tasks = cache.get(cache_key)

        if cached_tasks:
            return cached_tasks

        try:
            from tasks_app.api.serializers import TaskSerializer
            tasks = []
            for column in obj.columns.all():
                tasks.extend(column.tasks.all().select_related('assignee', 'created_by').prefetch_related('reviewers'))

            tasks_data = TaskSerializer(tasks, many=True, context=self.context).data

            cache.set(cache_key, tasks_data, 300)
            return tasks_data

        except Exception as e:
            return []

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Board title cannot be empty")
        return value.strip()

    def to_representation(self, instance):
        """Optimierte Representation mit reduziertem Logging."""
        data = super().to_representation(instance)

        if not hasattr(self.context.get('request', {}), '_board_serialized'):
            if hasattr(self.context.get('request', {}), 'user'):
                self.context['request']._board_serialized = True

        return data

    def update(self, instance, validated_data):
        """Update mit Cache-Clearing."""
        cache_patterns = [
            f"board_members_{instance.id}_*",
            f"board_columns_{instance.id}_*",
            f"board_tasks_{instance.id}_*",
            f"board_detail_{instance.id}_*"
        ]

        for pattern in cache_patterns:
            cache.delete_many([pattern])

        return super().update(instance, validated_data)

class BoardMembershipSerializer(serializers.ModelSerializer):
    """Serializer für Board-Membership mit User-Details."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BoardMembership
        fields = ['id', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']