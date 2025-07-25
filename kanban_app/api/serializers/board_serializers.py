from rest_framework import serializers
from django.contrib.auth.models import User

from kanban_app.models import Board, BoardMembership
from auth_app.api.serializers import UserSerializer


class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing boards with basic information and counts.
    
    Provides read-only fields for member count, ticket count, tasks to-do count,
    and high priority tasks count.
    """
    owner = UserSerializer(read_only=True)
    member_count = serializers.ReadOnlyField()
    ticket_count = serializers.ReadOnlyField()
    tasks_to_do_count = serializers.ReadOnlyField()
    tasks_high_prio_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Board
        fields = [
            'id', 'title', 'description', 'status', 'owner', 
            'member_count', 'ticket_count', 'tasks_to_do_count', 
            'tasks_high_prio_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        """
        Transform input data before validation.
        
        Args:
            data (dict): Input data to be validated
            
        Returns:
            dict: Transformed data with title mapped to name
        """
        if 'title' in data:
            data['name'] = data.pop('title')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """
        Transform instance data for output.
        
        Args:
            instance (Board): Board instance to serialize
            
        Returns:
            dict: Serialized data with name mapped to title
        """
        data = super().to_representation(instance)
        if 'name' in data:
            data['title'] = data.pop('name')
        return data


class BoardCreateSerializer(serializers.Serializer):
    """
    Serializer for creating new boards with members and default columns.
    
    Creates a board with the requesting user as admin and optional members as editors.
    Automatically creates default columns: To-do, In-progress, Review, Done.
    """
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )

    def create(self, validated_data):
        """
        Create a new board with members and default columns.
        
        Args:
            validated_data (dict): Validated data containing title, description, and member IDs
            
        Returns:
            Board: Created board instance
        """
        board = self._create_board(validated_data)
        self._create_admin_membership(board)
        self._add_members(board, validated_data.get('members', []))
        self._create_default_columns(board)
        return board

    def _create_board(self, validated_data):
        """
        Create the board instance.
        
        Args:
            validated_data (dict): Validated data
            
        Returns:
            Board: Created board instance
        """
        return Board.objects.create(
            title=validated_data.get('title'),
            description=validated_data.get('description', ''),
            owner=self.context['request'].user
        )

    def _create_admin_membership(self, board):
        """
        Create admin membership for the board owner.
        
        Args:
            board (Board): Board instance
        """
        BoardMembership.objects.create(
            user=self.context['request'].user,
            board=board,
            role='ADMIN'
        )

    def _add_members(self, board, member_ids):
        """
        Add members to the board as editors.
        
        Args:
            board (Board): Board instance
            member_ids (list): List of user IDs to add as members
        """
        for member_id in member_ids:
            try:
                user = User.objects.get(id=member_id)
                if user != self.context['request'].user:
                    BoardMembership.objects.get_or_create(
                        user=user,
                        board=board,
                        defaults={'role': 'EDITOR'}
                    )
            except User.DoesNotExist:
                continue

    def _create_default_columns(self, board):
        """
        Create default columns for the board.
        
        Args:
            board (Board): Board instance
        """
        from kanban_app.models import Column
        default_columns = [
            {'title': 'To-do', 'position': 0},
            {'title': 'In-progress', 'position': 1},
            {'title': 'Review', 'position': 2},
            {'title': 'Done', 'position': 3}
        ]
        
        for col_data in default_columns:
            Column.objects.create(
                board=board,
                title=col_data['title'],
                position=col_data['position']
            )

    def validate_title(self, value):
        """
        Validate board title is not empty.
        
        Args:
            value (str): Title value to validate
            
        Returns:
            str: Cleaned title value
            
        Raises:
            ValidationError: If title is empty or only whitespace
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Board title cannot be empty")
        return value.strip()


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for board information including members and tasks.
    
    Provides comprehensive board data with nested member information,
    task details, and owner information.
    """
    owner = UserSerializer(read_only=True)
    members = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    owner_id = serializers.ReadOnlyField()
    
    class Meta:
        model = Board
        fields = [
            'id', 'title', 'description', 'status', 'owner', 'owner_id',
            'members', 'tasks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        """
        Transform input data before validation.
        
        Args:
            data (dict): Input data to be validated
            
        Returns:
            dict: Transformed data with title mapped to name
        """
        if 'title' in data:
            data['name'] = data.pop('title')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """
        Transform instance data for output.
        
        Args:
            instance (Board): Board instance to serialize
            
        Returns:
            dict: Serialized data with name mapped to title
        """
        data = super().to_representation(instance)
        if 'name' in data:
            data['title'] = data.pop('name')
        return data

    def get_members(self, obj):
        """
        Get board members with their roles.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            list: List of member dictionaries with id, fullname, email, and role
        """
        memberships = obj.boardmembership_set.select_related('user').all()
        return self._format_members(memberships)

    def _format_members(self, memberships):
        """
        Format membership data for serialization.
        
        Args:
            memberships (QuerySet): BoardMembership queryset
            
        Returns:
            list: Formatted member data
        """
        return [{
            'id': membership.user.id,
            'fullname': self._get_user_fullname(membership.user),
            'email': membership.user.email,
            'role': membership.role
        } for membership in memberships]

    def get_tasks(self, obj):
        """
        Get all tasks for the board across all columns.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            list: List of task dictionaries with details
        """
        try:
            tasks = []
            for column in obj.columns.all():
                column_tasks = self._get_column_tasks(column)
                for task in column_tasks:
                    task_data = self._format_task_data(task, obj.id)
                    tasks.append(task_data)
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

    def _format_task_data(self, task, board_id):
        """
        Format task data for serialization.
        
        Args:
            task (Task): Task instance
            board_id (int): Board ID
            
        Returns:
            dict: Formatted task data
        """
        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'board': board_id,
            'assignee': self._format_assignee(task.assignee) if task.assignee else None,
            'reviewer': self._format_reviewer(task),
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        }
        return task_data

    def _format_assignee(self, assignee):
        """
        Format assignee data.
        
        Args:
            assignee (User): User instance
            
        Returns:
            dict: Formatted assignee data
        """
        return {
            'id': assignee.id,
            'fullname': self._get_user_fullname(assignee),
            'email': assignee.email
        }

    def _format_reviewer(self, task):
        """
        Format reviewer data for task.
        
        Args:
            task (Task): Task instance
            
        Returns:
            dict or None: Formatted reviewer data or None if no reviewer
        """
        reviewer = task.reviewers.first()
        if reviewer:
            return {
                'id': reviewer.id,
                'fullname': self._get_user_fullname(reviewer),
                'email': reviewer.email
            }
        return None

    def _get_user_fullname(self, user):
        """
        Get formatted fullname for user.
        
        Args:
            user (User): User instance
            
        Returns:
            str: Full name or username if name is empty
        """
        fullname = f"{user.first_name} {user.last_name}".strip()
        return fullname or user.username

    def validate_title(self, value):
        """
        Validate board title is not empty.
        
        Args:
            value (str): Title value to validate
            
        Returns:
            str: Cleaned title value
            
        Raises:
            ValidationError: If title is empty or only whitespace
        """
        if not value.strip():
            raise serializers.ValidationError("Board title cannot be empty")
        return value.strip()


class BoardMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for board membership information.
    
    Provides user details and role information for board memberships.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BoardMembership
        fields = ['id', 'user', 'role']