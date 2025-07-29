from rest_framework import serializers
from django.contrib.auth.models import User

from kanban_app.models import Board, BoardMembership
from auth_app.api.serializers import UserSerializer


class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for Board list view with summary information.
    
    Provides basic board information with computed counts for
    members, tickets, and task statistics.
    """
    
    owner = UserSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    ticket_count = serializers.ReadOnlyField()
    tasks_to_do_count = serializers.ReadOnlyField()
    tasks_high_prio_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Board
        fields = [
            'id', 'name', 'description', 'owner', 'member_count', 
            'ticket_count', 'tasks_to_do_count', 'tasks_high_prio_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'owner']

    def to_representation(self, instance):
        """
        Convert model instance to dictionary representation.
        
        Args:
            instance (Board): Board model instance
            
        Returns:
            dict: Serialized board data with name field from title
        """
        data = super().to_representation(instance)
        data['name'] = instance.title
        return data


class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new boards.
    
    Handles board creation with optional member assignment
    and validates required fields.
    """
    
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        write_only=True
    )
    title = serializers.CharField(max_length=100, required=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Board
        fields = ['title', 'description', 'members']


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Board model with complete information.
    
    Includes owner details, members with roles, columns, and all tasks
    with comprehensive nested data structures.
    """
    
    owner = UserSerializer(read_only=True)
    members = serializers.SerializerMethodField()
    columns = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            'id', 'name', 'description', 'owner', 'members', 'columns', 
            'tasks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']

    def get_members(self, obj):
        """
        Get formatted member information with roles.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            list: List of member dictionaries with user info and roles
        """
        try:
            memberships = obj.boardmembership_set.all().select_related('user')
            return self._format_memberships(memberships)
        except Exception:
            return []

    def _format_memberships(self, memberships):
        """
        Format membership data for serialization.
        
        Args:
            memberships (QuerySet): BoardMembership queryset
            
        Returns:
            list: Formatted membership data
        """
        return [{
            'id': membership.id,
            'user': self._format_user_data(membership.user),
            'role': membership.role
        } for membership in memberships]

    def _format_user_data(self, user):
        """
        Format user data for membership serialization.
        
        Args:
            user (User): User instance
            
        Returns:
            dict: Formatted user data
        """
        fullname = f"{user.first_name} {user.last_name}".strip()
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'fullname': fullname or user.username,
            'username': user.username
        }

    def get_columns(self, obj):
        """
        Get columns for the board with status mapping.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            list: List of column dictionaries with status information
        """
        try:
            columns = obj.columns.all().order_by('position')
            return self._format_columns(columns)
        except Exception:
            return []

    def _format_columns(self, columns):
        """
        Format columns data for serialization.
        
        Args:
            columns (QuerySet): Column queryset
            
        Returns:
            list: Formatted column data
        """
        return [{
            'id': column.id,
            'title': column.title,
            'name': column.title,
            'position': column.position,
            'status': self._get_column_status(column.title)
        } for column in columns]

    def _get_column_status(self, title):
        """
        Map column title to standardized status.
        
        Args:
            title (str): Column title
            
        Returns:
            str: Standardized status string
        """
        if not title:
            return 'TODO'
        
        title_lower = title.lower()
        status_mapping = {
            'todo': 'TODO',
            'to do': 'TODO',
            'to-do': 'TODO',
            'progress': 'IN_PROGRESS',
            'doing': 'IN_PROGRESS',
            'review': 'REVIEW',
            'done': 'DONE',
            'complete': 'DONE'
        }
        
        for key, status in status_mapping.items():
            if key in title_lower:
                return status
        return 'TODO'

    def get_tasks(self, obj):
        """
        Get all tasks for the board across all columns.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            list: List of task dictionaries with complete details
        """
        try:
            tasks = []
            for column in obj.columns.all():
                column_tasks = self._get_column_tasks(column)
                tasks.extend(self._format_tasks(column_tasks, obj.id))
            return tasks
        except Exception:
            return []

    def _get_column_tasks(self, column):
        """
        Get tasks for a specific column with related data.
        
        Args:
            column (Column): Column instance
            
        Returns:
            QuerySet: Tasks with prefetched related data
        """
        return column.tasks.all().select_related(
            'assignee', 'created_by'
        ).prefetch_related('reviewers')

    def _format_tasks(self, tasks, board_id):
        """
        Format tasks data for serialization.
        
        Args:
            tasks (QuerySet): Task queryset
            board_id (int): Board ID
            
        Returns:
            list: Formatted task data
        """
        return [{
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'due_date': task.due_date,
            'column_id': task.column.id,
            'assignee': self._format_user_data(task.assignee) if task.assignee else None,
            'created_by': self._format_user_data(task.created_by),
            'board_id': board_id,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        } for task in tasks]

    def to_representation(self, instance):
        """
        Convert model instance to dictionary representation.
        
        Args:
            instance (Board): Board model instance
            
        Returns:
            dict: Serialized board data with name field from title
        """
        data = super().to_representation(instance)
        data['name'] = instance.title
        return data


class BoardMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for BoardMembership model.
    
    Handles the relationship between users and boards with role information
    and provides user details through nested serialization.
    """
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BoardMembership
        fields = ['id', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']