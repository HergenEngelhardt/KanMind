from rest_framework import serializers
from django.contrib.auth.models import User

from tasks_app.models import Task, Comment
from auth_app.api.serializers import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
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
        return obj.column.board.id if obj.column and obj.column.board else None

    def get_reviewer(self, obj):
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
        return obj.comments.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Ensure assignee has fullname
        if 'assignee' in data and data['assignee']:
            assignee = data['assignee']
            if 'fullname' not in assignee:
                assignee['fullname'] = f"{assignee.get('first_name', '')} {assignee.get('last_name', '')}".strip() or assignee.get('username', '')
        
        return data

    def create(self, validated_data):
        board_id = self.context['request'].data.get('board')
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        
        if board_id:
            from kanban_app.models import Board
            try:
                board = Board.objects.get(id=board_id)
                status_to_column = {
                    'to-do': 'To-do',
                    'in-progress': 'In-progress', 
                    'review': 'Review',
                    'done': 'Done'
                }
                
                status = validated_data.get('status', 'to-do')
                column_name = status_to_column.get(status, 'To-do')
                
                column = board.columns.filter(name=column_name).first()
                if not column:
                    from kanban_app.models import Column
                    column = Column.objects.create(
                        name=column_name,
                        board=board,
                        position=0
                    )
            except Board.DoesNotExist:
                raise serializers.ValidationError("Board not found")
        else:
            raise serializers.ValidationError("Board ID is required")
        
        task = Task.objects.create(
            column=column,
            assignee_id=assignee_id,
            created_by=self.context['request'].user,
            **validated_data
        )
        
        if reviewer_id:
            try:
                reviewer = User.objects.get(id=reviewer_id)
                task.reviewers.add(reviewer)
            except User.DoesNotExist:
                pass
        
        return task

    def update(self, instance, validated_data):
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        
        if assignee_id is not None:
            instance.assignee_id = assignee_id
        
        if reviewer_id is not None:
            instance.reviewers.clear()
            if reviewer_id:
                try:
                    reviewer = User.objects.get(id=reviewer_id)
                    instance.reviewers.add(reviewer)
                except User.DoesNotExist:
                    pass
        
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        if old_status != new_status and instance.column:
            status_to_column = {
                'to-do': 'To-do',
                'in-progress': 'In-progress',
                'review': 'Review', 
                'done': 'Done'
            }
            
            column_name = status_to_column.get(new_status, 'To-do')
            new_column = instance.column.board.columns.filter(name=column_name).first()
            
            if new_column:
                instance.column = new_column
            
        return super().update(instance, validated_data)