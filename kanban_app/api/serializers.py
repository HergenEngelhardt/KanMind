from rest_framework import serializers
from django.contrib.auth.models import User
from kanban_app.models import Board, BoardMembership, Column


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    fullname = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'fullname']
        
    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email


class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for board list view.
    
    Provides basic board information for listing purposes.
    Includes owner details but excludes detailed relationships.
    Supports both 'name' and 'title' fields for frontend compatibility.
    """
    
    owner = UserSerializer(read_only=True)
    title = serializers.CharField(write_only=True, required=False, help_text="Alternative field name for 'name'")

    class Meta:
        model = Board
        fields = [
            "id", 
            "name", 
            "title",
            "description", 
            "owner", 
            "created_at", 
            "updated_at"
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Custom validation to handle title->name conversion and ensure name is provided.
        
        Args:
            data (dict): Input data
            
        Returns:
            dict: Validated data with name field
            
        Raises:
            ValidationError: If neither name nor title is provided or both are empty
        """
        if 'title' in data and 'name' not in data:
            data['name'] = data['title']
        elif 'title' in data and 'name' in data:
            pass
        
        if 'title' in data:
            del data['title']
        
        if not data.get('name', '').strip():
            raise serializers.ValidationError({
                'name': 'Board name is required and cannot be empty.'
            })
        
        data['name'] = data['name'].strip()
        
        return data

    def validate_name(self, value):
        """
        Validate board name is not empty.
        
        Args:
            value (str): Board name
            
        Returns:
            str: Validated name
            
        Raises:
            ValidationError: If name is empty or whitespace only
        """
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Board name cannot be empty."
            )
        return value.strip()


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


class ColumnSerializer(serializers.ModelSerializer):
    """
    Serializer for board columns.
    
    Includes associated tasks for complete column representation.
    Board field is read-only to prevent unauthorized modifications.
    """
    from tasks_app.api.serializers import TaskSerializer
    tasks = TaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = Column
        fields = ["id", "name", "position", "board", "tasks"]
        read_only_fields = ["board"]

    def validate_position(self, value):
        """
        Validate column position is positive.
        
        Args:
            value (int): Position value
            
        Returns:
            int: Validated position
            
        Raises:
            ValidationError: If position is not positive
        """
        if value < 1:
            raise serializers.ValidationError(
                "Position must be a positive integer."
            )
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
    columns = ColumnSerializer(many=True, read_only=True)
    title = serializers.CharField(write_only=True, required=False, help_text="Alternative field name for 'name'")

class Meta:
    model = Board
    fields = [
        "id",
        "name",
        "title",
        "description",
        "owner",
        "members",
        "columns",
        "created_at",
        "updated_at",
    ]
    read_only_fields = ['id', 'owner', 'members', 'columns', 'created_at', 'updated_at']

def _serialize_user(self, user):
    """Helper method to serialize user data."""
    if not user:
        return {
            'id': None,
            'email': '',
            'first_name': '',
            'last_name': '',
            'username': '',
            'fullname': ''
        }
    
    return {
        'id': user.id,
        'email': user.email or '',
        'first_name': user.first_name or '',
        'last_name': user.last_name or '',
        'username': user.username or '',
        'fullname': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email or ''
    }

def _serialize_members(self, instance):
    """Helper method to serialize board members."""
    members = []
    if hasattr(instance, 'boardmembership_set'):
        for membership in instance.boardmembership_set.all():
            if membership.user:
                member_data = {
                    'id': membership.id,
                    'role': membership.role or 'VIEWER',
                    'user': self._serialize_user(membership.user)
                }
                members.append(member_data)
    return members

def _serialize_task(self, task):
    """Helper method to serialize task data."""
    task_data = {
        'id': task.id,
        'title': task.title or '',
        'description': task.description or '',
        'position': task.position or 0,
        'status': getattr(task, 'status', 'TODO'),
        'created_at': task.created_at.isoformat() if task.created_at else None,
        'updated_at': task.updated_at.isoformat() if task.updated_at else None,
        'assignee': self._serialize_user(getattr(task, 'assignee', None)),
        'reviewers': []
    }
    
    if hasattr(task, 'reviewers'):
        task_data['reviewers'] = [
            self._serialize_user(reviewer) 
            for reviewer in task.reviewers.all()
        ]
    
    return task_data

def _serialize_columns(self, instance):
    """Helper method to serialize board columns."""
    columns = []
    if hasattr(instance, 'columns'):
        for column in instance.columns.all().order_by('position'):
            column_data = {
                'id': column.id,
                'name': column.name or '',
                'position': column.position or 0,
                'board': column.board_id,
                'tasks': []
            }
            
            if hasattr(column, 'tasks'):
                column_data['tasks'] = [
                    self._serialize_task(task) 
                    for task in column.tasks.all().order_by('position')
                ]
            
            columns.append(column_data)
    return columns

def to_representation(self, instance):
    """Ensure all data fields are properly formatted for frontend."""
    try:
        data = super().to_representation(instance)
        
        data.update({
            'id': instance.id,
            'name': instance.name or '',
            'description': instance.description or '',
            'created_at': instance.created_at.isoformat() if instance.created_at else None,
            'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
            'owner': self._serialize_user(instance.owner),
            'members': self._serialize_members(instance),
            'columns': self._serialize_columns(instance)
        })
        
        return data
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Board serialization error: {str(e)}")
        
        return {
            'id': getattr(instance, 'id', None),
            'name': getattr(instance, 'name', ''),
            'description': getattr(instance, 'description', ''),
            'owner': None,
            'members': [],
            'columns': [],
            'created_at': None,
            'updated_at': None
    }