from rest_framework import serializers
from django.contrib.auth.models import User

from tasks_app.models import Task, Comment
from auth_app.api.serializers import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model with author information.
    """
    author = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']
    
    def get_author(self, obj):
        """
        Get author full name or username for the comment.
        
        Args:
            obj (Comment): Comment instance
            
        Returns:
            str: Author's full name or username
        """
        user = obj.created_by
        fullname = f"{user.first_name} {user.last_name}".strip()
        return fullname if fullname else user.username


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model with related user information and board details.
    """
    assignee = UserSerializer(read_only=True)
    reviewer = serializers.SerializerMethodField()
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    comments_count = serializers.SerializerMethodField()
    board = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'assignee_id', 'reviewer_id',
            'due_date', 'comments_count', 'board', 'created_at', 'updated_at'
        ]

    def get_board(self, obj):
        """
        Get the board ID associated with the task.
        
        Args:
            obj (Task): Task instance
            
        Returns:
            int or None: Board ID if exists, None otherwise
        """
        return obj.column.board.id if obj.column and obj.column.board else None

    def get_reviewer(self, obj):
        """
        Get reviewer information for the task.
        
        Args:
            obj (Task): Task instance
            
        Returns:
            dict or None: Reviewer details if exists, None otherwise
        """
        if not obj.reviewers.exists():
            return None
            
        reviewer = obj.reviewers.first()
        return {
            'id': reviewer.id,
            'fullname': f"{reviewer.first_name} {reviewer.last_name}".strip() or reviewer.username,
            'email': reviewer.email,
            'username': reviewer.username
        }

    def get_comments_count(self, obj):
        """
        Get the count of comments for the task.
        
        Args:
            obj (Task): Task instance
            
        Returns:
            int: Number of comments
        """
        return obj.comments.count()

    def to_representation(self, instance):
        """
        Customize the representation to include assignee fullname.
        
        Args:
            instance (Task): Task instance
            
        Returns:
            dict: Serialized data with additional fullname field
        """
        data = super().to_representation(instance)
        
        if 'assignee' in data and data['assignee']:
            assignee = data['assignee']
            if 'fullname' not in assignee:
                user = instance.assignee
                assignee['fullname'] = f"{user.first_name} {user.last_name}".strip() or user.username
        
        return data

    def _get_board_column(self, board_id):
        """
        Get the first column of a board.
        
        Args:
            board_id (int): Board ID
            
        Returns:
            Column: First column of the board
            
        Raises:
            serializers.ValidationError: If board not found or has no columns
        """
        from kanban_app.models import Board
        try:
            board = Board.objects.get(id=board_id)
            column = board.columns.first()
            if not column:
                raise serializers.ValidationError("Board has no columns")
            return column
        except Board.DoesNotExist:
            raise serializers.ValidationError("Board not found")

    def _assign_reviewer(self, task, reviewer_id):
        """
        Assign a reviewer to the task.
        
        Args:
            task (Task): Task instance
            reviewer_id (int): Reviewer user ID
        """
        if reviewer_id:
            try:
                reviewer = User.objects.get(id=reviewer_id)
                task.reviewers.add(reviewer)
            except User.DoesNotExist:
                pass

    def create(self, validated_data):
        """
        Create a new task with board assignment.
        
        Args:
            validated_data (dict): Validated task data
            
        Returns:
            Task: Created task instance
            
        Raises:
            serializers.ValidationError: If board ID missing or invalid
        """
        board_id = self.context['request'].data.get('board')
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        
        if not board_id:
            raise serializers.ValidationError("Board ID is required")
        
        column = self._get_board_column(board_id)
        
        task = Task.objects.create(
            column=column,
            assignee_id=assignee_id,
            created_by=self.context['request'].user,
            **validated_data
        )
        
        self._assign_reviewer(task, reviewer_id)
        return task

    def _update_column_by_status(self, instance, new_status):
        """
        Update task column based on status change.
        
        Args:
            instance (Task): Task instance
            new_status (str): New status value
        """
        if not instance.column:
            return
            
        from kanban_app.models import Column
        status_to_column = {
            'to-do': 'To-do',
            'in-progress': 'In-progress', 
            'review': 'Review',
            'done': 'Done'
        }
        column_title = status_to_column.get(new_status)
        if column_title:
            try:
                new_column = Column.objects.get(
                    board=instance.column.board,
                    title=column_title 
                )
                instance.column = new_column
            except Column.DoesNotExist:
                pass

    def update(self, instance, validated_data):
        """
        Update an existing task.
        
        Args:
            instance (Task): Task instance to update
            validated_data (dict): Validated update data
            
        Returns:
            Task: Updated task instance
        """
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        
        if assignee_id is not None:
            instance.assignee_id = assignee_id
        
        if reviewer_id is not None:
            instance.reviewers.clear()
            self._assign_reviewer(instance, reviewer_id)
        
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        if old_status != new_status:
            self._update_column_by_status(instance, new_status)
        
        return super().update(instance, validated_data)


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating tasks with column management.
    """
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee_id', 'reviewer_id', 'due_date', 'column'
        ]

    def _update_assignee(self, instance, assignee_id):
        """
        Update task assignee.
        
        Args:
            instance (Task): Task instance
            assignee_id (int or None): Assignee user ID
        """
        if assignee_id is not None:
            instance.assignee_id = assignee_id

    def _update_reviewer(self, instance, reviewer_id):
        """
        Update task reviewer.
        
        Args:
            instance (Task): Task instance
            reviewer_id (int or None): Reviewer user ID
        """
        if reviewer_id is not None:
            instance.reviewers.clear()
            if reviewer_id:
                try:
                    reviewer = User.objects.get(id=reviewer_id)
                    instance.reviewers.add(reviewer)
                except User.DoesNotExist:
                    pass

    def _update_column_by_status(self, instance, old_status, new_status):
        """
        Update column based on status change.
        
        Args:
            instance (Task): Task instance
            old_status (str): Previous status
            new_status (str): New status
        """
        if old_status == new_status or not instance.column:
            return
            
        from kanban_app.models import Column
        status_to_column = {
            'to-do': 'To-do',
            'in-progress': 'In-progress', 
            'review': 'Review',
            'done': 'Done'
        }
        column_title = status_to_column.get(new_status)
        if column_title:
            try:
                new_column = Column.objects.get(
                    board=instance.column.board,
                    title=column_title 
                )
                instance.column = new_column
            except Column.DoesNotExist:
                pass
        
    def update(self, instance, validated_data):
        """
        Update task instance with all provided data.
        
        Args:
            instance (Task): Task instance to update
            validated_data (dict): Validated update data
            
        Returns:
            Task: Updated task instance
        """
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        
        self._update_assignee(instance, assignee_id)
        self._update_reviewer(instance, reviewer_id)
        
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        self._update_column_by_status(instance, old_status, new_status)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
                
        instance.save()
        return instance