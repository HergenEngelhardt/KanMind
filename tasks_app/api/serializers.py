from rest_framework import serializers
from django.contrib.auth.models import User

from tasks_app.models import Task, Comment
from auth_app.api.serializers import UserSerializer
from kanban_app.models import Column


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model with author information.
    
    Handles serialization of comment data including author details
    and provides custom author name formatting.
    """
    
    created_by = UserSerializer(read_only=True)
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'content', 'created_by', 'author_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_author_name(self, obj):
        """
        Get the formatted author name for the comment.
        
        Args:
            obj (Comment): Comment instance
            
        Returns:
            str: Formatted author name
        """
        return obj.get_author_name()


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model with comprehensive task information.
    
    Handles task serialization including assignee, reviewer, board information,
    and comment count with support for user assignment operations.
    """
    
    assignee = UserSerializer(read_only=True)
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    created_by = UserSerializer(read_only=True)
    board = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'priority', 'status', 'due_date',
            'column', 'assignee', 'assignee_id', 'reviewer_id',
            'created_by', 'board', 'comments_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_board(self, obj):
        """
        Get board information from the task's column.
        
        Args:
            obj (Task): Task instance
            
        Returns:
            dict or None: Board information with id and name
        """
        if obj.column and obj.column.board:
            return {
                'id': obj.column.board.id,
                'name': obj.column.board.title
            }
        return None

    def get_comments_count(self, obj):
        """
        Get the count of comments for the task.
        
        Args:
            obj (Task): Task instance
            
        Returns:
            int: Number of comments on the task
        """
        return obj.comments.count()

    def create(self, validated_data):
        """
        Create a new task with assignee and reviewer assignment.
        
        Args:
            validated_data (dict): Validated task data
            
        Returns:
            Task: Created task instance
        """
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        
        validated_data['created_by'] = self.context['request'].user
        task = Task.objects.create(**validated_data)
        
        self._assign_task_users(task, assignee_id, reviewer_id)
        return task

    def _assign_task_users(self, task, assignee_id, reviewer_id):
        """
        Assign users to the task as assignee and reviewer.
        
        Args:
            task (Task): Task instance to assign users to
            assignee_id (int or None): ID of user to assign as assignee
            reviewer_id (int or None): ID of user to assign as reviewer
        """
        if assignee_id:
            self._assign_user_to_task(task, assignee_id, 'assignee')
        
        if reviewer_id:
            self._assign_reviewer_to_task(task, reviewer_id)

    def _assign_user_to_task(self, task, user_id, role):
        """
        Assign a user to a task in a specific role.
        
        Args:
            task (Task): Task instance
            user_id (int): User ID to assign
            role (str): Role to assign ('assignee')
        """
        try:
            user = User.objects.get(id=user_id)
            setattr(task, role, user)
            task.save()
        except User.DoesNotExist:
            pass

    def _assign_reviewer_to_task(self, task, reviewer_id):
        """
        Assign a reviewer to the task.
        
        Args:
            task (Task): Task instance
            reviewer_id (int): ID of user to assign as reviewer
        """
        try:
            reviewer = User.objects.get(id=reviewer_id)
            task.reviewers.add(reviewer)
        except User.DoesNotExist:
            pass

    def update(self, instance, validated_data):
        """
        Update an existing task with new assignee and reviewer data.
        
        Args:
            instance (Task): Task instance to update
            validated_data (dict): Validated update data
            
        Returns:
            Task: Updated task instance
        """
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        
        self._update_task_assignee(instance, assignee_id)
        self._update_task_reviewer(instance, reviewer_id)
        
        return super().update(instance, validated_data)

    def _update_task_assignee(self, instance, assignee_id):
        """
        Update the task assignee.
        
        Args:
            instance (Task): Task instance to update
            assignee_id (int or None): New assignee ID or None to clear
        """
        if assignee_id is not None:
            if assignee_id:
                self._assign_user_to_task(instance, assignee_id, 'assignee')
            else:
                instance.assignee = None
                instance.save()

    def _update_task_reviewer(self, instance, reviewer_id):
        """
        Update the task reviewer.
        
        Args:
            instance (Task): Task instance to update
            reviewer_id (int or None): New reviewer ID or None to clear
        """
        if reviewer_id is not None:
            instance.reviewers.clear()
            if reviewer_id:
                self._assign_reviewer_to_task(instance, reviewer_id)