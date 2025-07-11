from rest_framework import serializers
from django.contrib.auth.models import User

from kanban_app.models import Board, BoardMembership
from auth_app.api.serializers import UserSerializer


class BoardListSerializer(serializers.ModelSerializer):
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
        if 'title' in data:
            data['name'] = data.pop('title')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if 'name' in data:
            data['title'] = data.pop('name')
        return data


class BoardCreateSerializer(serializers.Serializer):  # Verwende Serializer statt ModelSerializer
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    members = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )

    def create(self, validated_data):
        title = validated_data.get('title')
        description = validated_data.get('description', '')
        member_ids = validated_data.get('members', [])
        
        # Board erstellen
        board = Board.objects.create(
            title=title,
            description=description,
            owner=self.context['request'].user
        )
        
        # Erstelle Admin-Membership für den Owner
        BoardMembership.objects.create(
            user=self.context['request'].user,
            board=board,
            role='ADMIN'
        )
        
        # Füge andere Mitglieder hinzu
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
        
        # Erstelle Standard-Spalten
        from kanban_app.models import Column
        default_columns = [
            {'name': 'To-do', 'position': 0},
            {'name': 'In-progress', 'position': 1},
            {'name': 'Review', 'position': 2},
            {'name': 'Done', 'position': 3}
        ]
        
        for col_data in default_columns:
            Column.objects.create(
                board=board,
                name=col_data['name'],
                position=col_data['position']
            )
        
        return board

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Board title cannot be empty")
        return value.strip()


class BoardDetailSerializer(serializers.ModelSerializer):
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
        if 'title' in data:
            data['name'] = data.pop('title')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if 'name' in data:
            data['title'] = data.pop('name')
        return data

    def get_members(self, obj):
        memberships = obj.boardmembership_set.select_related('user').all()
        return [{
            'id': membership.user.id,
            'fullname': f"{membership.user.first_name} {membership.user.last_name}".strip() or membership.user.username,
            'email': membership.user.email,
            'role': membership.role
        } for membership in memberships]

    def get_tasks(self, obj):
        try:
            from tasks_app.models import Task
            tasks = []
            for column in obj.columns.all():
                column_tasks = column.tasks.all().select_related('assignee', 'created_by').prefetch_related('reviewers')
                for task in column_tasks:
                    task_data = {
                        'id': task.id,
                        'title': task.title,
                        'description': task.description,
                        'status': task.status,
                        'priority': task.priority,
                        'due_date': task.due_date.isoformat() if task.due_date else None,
                        'board': obj.id,
                        'assignee': None,
                        'reviewer': None,
                        'created_at': task.created_at.isoformat(),
                        'updated_at': task.updated_at.isoformat()
                    }
                    
                    if task.assignee:
                        task_data['assignee'] = {
                            'id': task.assignee.id,
                            'fullname': f"{task.assignee.first_name} {task.assignee.last_name}".strip() or task.assignee.username,
                            'email': task.assignee.email
                        }
                    
                    reviewer = task.reviewers.first()
                    if reviewer:
                        task_data['reviewer'] = {
                            'id': reviewer.id,
                            'fullname': f"{reviewer.first_name} {reviewer.last_name}".strip() or reviewer.username,
                            'email': reviewer.email
                        }
                    
                    tasks.append(task_data)
            
            return tasks
        except Exception:
            return []

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Board title cannot be empty")
        return value.strip()


class BoardMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BoardMembership
        fields = ['id', 'user', 'role']