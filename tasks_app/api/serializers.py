from rest_framework import serializers
from tasks_app.models import Task, Comment
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from kanban_app.models import BoardMembership
from django.shortcuts import get_object_or_404


User = get_user_model()

class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for task model.
    """
    assignee_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    reviewer_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    assignee = serializers.SerializerMethodField(read_only=True)
    reviewer = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)
    board = serializers.PrimaryKeyRelatedField(read_only=True, source='column.board')
    
    class Meta:
        model = Task
        fields = ['id', 'board', 'title', 'description', 'status', 'priority', 
                 'assignee_id', 'assignee', 'reviewer_id', 'reviewer', 
                 'due_date', 'comments_count']
    
    def get_assignee(self, obj):
        """
        Gets assignee user data.
        
        Args:
            obj: Task instance
            
        Returns:
            dict: User data or None
        """
        if obj.assignee:
            return self._format_user_data(obj.assignee)
        return None
    
    def get_reviewer(self, obj):
        """
        Gets first reviewer user data.
        
        Args:
            obj: Task instance
            
        Returns:
            dict: User data or None
        """
        if obj.reviewers.exists():
            reviewer = obj.reviewers.first()
            return self._format_user_data(reviewer)
        return None
    
    def get_comments_count(self, obj):
        """
        Gets count of comments on task.
        
        Args:
            obj: Task instance
            
        Returns:
            int: Comment count
        """
        return obj.comments.count()
    
    def _format_user_data(self, user):
        """
        Formats user data for serialization.
        
        Args:
            user: User instance
            
        Returns:
            dict: Formatted user data
        """
        return {
            'id': user.id,
            'email': user.email,
            'fullname': f"{user.first_name} {user.last_name}".strip()
        }
    
    def validate(self, attrs):
        """
        Validates task status and priority.
        
        Args:
            attrs: Serializer attributes
            
        Returns:
            dict: Validated attributes
            
        Raises:
            ValidationError: If status or priority is invalid
        """
        self._validate_status(attrs)
        self._validate_priority(attrs)
        return attrs
    
    def _validate_status(self, attrs):
        """
        Validates task status.
        
        Args:
            attrs: Serializer attributes
            
        Raises:
            ValidationError: If status is invalid
        """
        status_value = attrs.get('status')
        if status_value and status_value not in ['to-do', 'in-progress', 'review', 'done']:
            raise serializers.ValidationError({"status": "Invalid status value"})
    
    def _validate_priority(self, attrs):
        """
        Validates task priority.
        
        Args:
            attrs: Serializer attributes
            
        Raises:
            ValidationError: If priority is invalid
        """
        priority_value = attrs.get('priority')
        if priority_value and priority_value not in ['low', 'medium', 'high']:
            raise serializers.ValidationError({"priority": "Invalid priority value"})
    
    def create(self, validated_data):
        """
        Creates a new task.
        
        Args:
            validated_data: Validated data
            
        Returns:
            Task: Created task instance
        """
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        
        validated_data['created_by'] = self.context['request'].user
        
        task = Task.objects.create(**validated_data)
        self._update_task_assignee(task, assignee_id)
        self._update_task_reviewer(task, reviewer_id)
        
        return task
    
    def update(self, instance, validated_data):
        """
        Updates a task instance.
        
        Args:
            instance: Task instance
            validated_data: Validated data
            
        Returns:
            Task: Updated task instance
        """
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        self._update_task_assignee(instance, assignee_id)
        self._update_task_reviewer(instance, reviewer_id)
        
        instance.save()
        return instance
    
    def _update_task_assignee(self, task, assignee_id):
        """
        Updates task assignee.
        
        Args:
            task: Task instance
            assignee_id: User ID or None
        """
        if assignee_id is not None:
            if assignee_id:
                try:
                    assignee = User.objects.get(id=assignee_id)
                    task.assignee = assignee
                except User.DoesNotExist:
                    pass
            else:
                task.assignee = None
    
    def _update_task_reviewer(self, task, reviewer_id):
        """
        Updates task reviewer.
        
        Args:
            task: Task instance
            reviewer_id: User ID or None
        """
        if reviewer_id is not None:
            task.reviewers.clear()
            if reviewer_id:
                try:
                    reviewer = User.objects.get(id=reviewer_id)
                    task.reviewers.add(reviewer)
                except User.DoesNotExist:
                    pass

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments.
    """
    author = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
    
    def get_author(self, obj):
        """
        Gets comment author's full name.
        
        Args:
            obj: Comment instance
            
        Returns:
            str: Author's full name
        """
        user = obj.created_by
        return f"{user.first_name} {user.last_name}".strip()


class CommentListCreateView(APIView):
    """
    View for listing and creating comments.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, task_id):
        """
        Lists comments for a task.
        
        Args:
            request: HTTP request
            task_id: ID of task to get comments for
            
        Returns:
            Response: JSON list of comments
        """
        task = self._get_task_if_authorized(task_id, request.user)
        if isinstance(task, Response):
            return task
        
        comments = Comment.objects.filter(task=task).order_by('created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, task_id):
        """
        Creates a comment on a task.
        
        Args:
            request: HTTP request with comment data
            task_id: ID of task to comment on
            
        Returns:
            Response: JSON with created comment or errors
        """
        task = self._get_task_if_authorized(task_id, request.user)
        if isinstance(task, Response):
            return task
        
        content = request.data.get('content')
        if not content:
            return Response(
                {'error': 'Content is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = self._create_comment(task, request.user, content)
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _get_task_if_authorized(self, task_id, user):
        """
        Retrieves task if user is authorized.
        
        Args:
            task_id: Task ID
            user: User requesting access
            
        Returns:
            Task or Response: Task if authorized, error Response if not
        """
        task = get_object_or_404(Task, id=task_id)
        board = task.column.board
        
        if board.owner != user and not BoardMembership.objects.filter(
                board=board, user=user
            ).exists():
            return Response(
                {'error': 'No permission to access this task'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return task
    
    def _create_comment(self, task, user, content):
        """
        Creates a new comment.
        
        Args:
            task: Task instance
            user: User creating comment
            content: Comment text
            
        Returns:
            Comment: Created comment
        """
        return Comment.objects.create(
            task=task,
            created_by=user,
            content=content
        )


class CommentDeleteView(APIView):
    """
    View for deleting comments.
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, task_id, comment_id):
        """
        Deletes a comment if user is author.
        
        Args:
            request: HTTP request
            task_id: Task ID
            comment_id: Comment ID to delete
            
        Returns:
            Response: Empty response on success, error otherwise
        """
        try:
            comment = get_object_or_404(Comment, id=comment_id, task_id=task_id)
            
            if comment.created_by != request.user:
                return Response(
                    {'error': 'Only the comment author can delete this comment'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            comment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except Comment.DoesNotExist:
            return Response(
                {'error': 'Comment not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )