from rest_framework import serializers
from kanban_app.models import Board, BoardMembership
from .user_serializers import UserSerializer
import logging

logger = logging.getLogger(__name__)


class BoardMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for board membership relationships.
    
    Represents user roles within a board.
    Used for displaying board members and their permissions.
    """
    
    user = UserSerializer(read_only=True)

    class Meta:
        model = BoardMembership
        fields = ["id", "user", "role"]


class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for board list view.
    
    Provides basic board information for listing purposes.
    Includes owner details but excludes detailed relationships.
    Supports both 'name' and 'title' fields for frontend compatibility.
    """
    
    owner = UserSerializer(read_only=True)
    title = serializers.CharField(write_only=True, required=False, help_text="Alternative field name for 'name'")
    deadline = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = Board
        fields = ["id", "name", "title", "description", "owner", "status", "deadline", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def validate(self, data):
        """Handle both 'name' and 'title' fields."""
        title = data.pop('title', None)
        if title and not data.get('name'):
            data['name'] = title
        return data

    def validate_name(self, value):
        """Validate board name is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Board name cannot be empty.")
        return value.strip()

    def validate_status(self, value):
        """Validate board status."""
        valid_statuses = ['PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual board view.
    
    Includes complete board information with members, columns, and tasks.
    Used for board detail and edit operations.
    Supports both 'name' and 'title' fields for frontend compatibility.
    """
    
    owner = UserSerializer(read_only=True)
    members = BoardMembershipSerializer(
        source="boardmembership_set", 
        many=True, 
        read_only=True
    )
    title = serializers.CharField(write_only=True, required=False, help_text="Alternative field name for 'name'")
    deadline = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = Board
        fields = ["id", "name", "title", "description", "owner", "members", "status", "deadline", "columns", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def validate(self, data):
        """Handle both 'name' and 'title' fields."""
        title = data.pop('title', None)
        if title and not data.get('name'):
            data['name'] = title
        return data

    def validate_name(self, value):
        """Validate board name is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Board name cannot be empty.")
        return value.strip()

    def validate_status(self, value):
        """Validate board status."""
        valid_statuses = ['PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value

    def _serialize_user(self, user):
        """Helper method to serialize user data safely."""
        if not user:
            return None
        
        try:
            return {
                'id': user.id,
                'email': getattr(user, 'email', ''),
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'username': getattr(user, 'username', ''),
                'fullname': f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
            }
        except Exception as e:
            logger.error(f"User serialization error: {str(e)}")
            return None

    def _serialize_members(self, board):
        """Helper method to serialize board members safely."""
        try:
            memberships = board.boardmembership_set.all()
            return [
                {
                    'id': membership.id,
                    'user': self._serialize_user(membership.user),
                    'role': membership.role
                }
                for membership in memberships
            ]
        except Exception as e:
            logger.error(f"Members serialization error: {str(e)}")
            return []

    def _serialize_columns(self, board):
        """Helper method to serialize board columns safely."""
        try:
            columns = board.columns.all().order_by('position')
            return [
                {
                    'id': column.id,
                    'name': column.name,
                    'position': column.position,
                    'tasks': self._serialize_column_tasks(column)
                }
                for column in columns
            ]
        except Exception as e:
            logger.error(f"Columns serialization error: {str(e)}")
            return []

    def _serialize_column_tasks(self, column):
        """Helper method to serialize tasks for a column safely."""
        try:
            from tasks_app.models import Task
            tasks = Task.objects.filter(column=column).order_by('position')
            return [
                {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'position': task.position,
                    'status': getattr(task, 'status', 'TODO'),
                    'assignee': self._serialize_user(task.assignee) if task.assignee else None,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'updated_at': task.updated_at.isoformat() if task.updated_at else None
                }
                for task in tasks
            ]
        except Exception as e:
            logger.error(f"Tasks serialization error: {str(e)}")
            return []

    def to_representation(self, instance):
        """Ensure all data fields are properly formatted for frontend."""
        try:
            data = super().to_representation(instance)
            
            data.update({
                'id': instance.id,
                'name': instance.name or '',
                'description': instance.description or '',
                'status': instance.status or 'PLANNING',
                'deadline': instance.deadline.isoformat() if instance.deadline else None,
                'created_at': instance.created_at.isoformat() if instance.created_at else None,
                'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
                'owner': self._serialize_user(instance.owner),
                'members': self._serialize_members(instance),
                'columns': self._serialize_columns(instance)
            })
            
            return data
            
        except Exception as e:
            logger.error(f"Board serialization error: {str(e)}")
            
            return {
                'id': getattr(instance, 'id', None),
                'name': getattr(instance, 'name', ''),
                'description': getattr(instance, 'description', ''),
                'status': getattr(instance, 'status', 'PLANNING'),
                'deadline': None,
                'owner': None,
                'members': [],
                'columns': [],
                'created_at': None,
                'updated_at': None
            }