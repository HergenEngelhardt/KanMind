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

    def to_representation(self, instance):
        """Ensure all data fields are properly formatted for frontend."""
        try:
            data = super().to_representation(instance)
            
            data['id'] = instance.id
            data['name'] = instance.name or ''
            data['description'] = instance.description or ''
            data['created_at'] = instance.created_at.isoformat() if instance.created_at else None
            data['updated_at'] = instance.updated_at.isoformat() if instance.updated_at else None
            
            if instance.owner:
                data['owner'] = {
                    'id': instance.owner.id,
                    'email': instance.owner.email or '',
                    'first_name': instance.owner.first_name or '',
                    'last_name': instance.owner.last_name or '',
                    'username': instance.owner.username or '',
                    'fullname': f"{instance.owner.first_name or ''} {instance.owner.last_name or ''}".strip() or instance.owner.email or ''
                }
            else:
                data['owner'] = {
                    'id': None,
                    'email': '',
                    'first_name': '',
                    'last_name': '',
                    'username': '',
                    'fullname': ''
                }
            
            data['members'] = []
            if hasattr(instance, 'boardmembership_set'):
                for membership in instance.boardmembership_set.all():
                    if membership.user:
                        member_data = {
                            'id': membership.id,
                            'role': membership.role or 'VIEWER',
                            'user': {
                                'id': membership.user.id,
                                'email': membership.user.email or '',
                                'first_name': membership.user.first_name or '',
                                'last_name': membership.user.last_name or '',
                                'username': membership.user.username or '',
                                'fullname': f"{membership.user.first_name or ''} {membership.user.last_name or ''}".strip() or membership.user.email or ''
                            }
                        }
                        data['members'].append(member_data)
            
            data['columns'] = []
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
                        for task in column.tasks.all().order_by('position'):
                            task_data = {
                                'id': task.id,
                                'title': task.title or '',
                                'description': task.description or '',
                                'position': task.position or 0,
                                'status': getattr(task, 'status', 'TODO'),
                                'created_at': task.created_at.isoformat() if task.created_at else None,
                                'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                                'assignee': None,
                                'reviewers': []
                            }
                            
                            if hasattr(task, 'assignee') and task.assignee:
                                task_data['assignee'] = {
                                    'id': task.assignee.id,
                                    'email': task.assignee.email or '',
                                    'first_name': task.assignee.first_name or '',
                                    'last_name': task.assignee.last_name or '',
                                    'username': task.assignee.username or '',
                                    'fullname': f"{task.assignee.first_name or ''} {task.assignee.last_name or ''}".strip() or task.assignee.email or ''
                                }
                            
                            # Reviewers hinzufügen
                            if hasattr(task, 'reviewers'):
                                for reviewer in task.reviewers.all():
                                    reviewer_data = {
                                        'id': reviewer.id,
                                        'email': reviewer.email or '',
                                        'first_name': reviewer.first_name or '',
                                        'last_name': reviewer.last_name or '',
                                        'username': reviewer.username or '',
                                        'fullname': f"{reviewer.first_name or ''} {reviewer.last_name or ''}".strip() or reviewer.email or ''
                                    }
                                    task_data['reviewers'].append(reviewer_data)
                            
                            column_data['tasks'].append(task_data)
                    
                    data['columns'].append(column_data)
            
            return data
            
        except Exception as e:
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
    def validate(self, data):
        """Handle title to name conversion."""
        if 'title' in data and 'name' not in data:
            data['name'] = data['title']
        if 'title' in data:
            del data['title']
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