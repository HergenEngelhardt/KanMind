from rest_framework import serializers
import logging

from ...models import Board, BoardMembership
from .user_serializers import UserSerializer
from .column_serializers import ColumnSerializer

logger = logging.getLogger(__name__)


class BoardMembershipSerializer(serializers.ModelSerializer):
    """Serializer for board membership relationships."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BoardMembership
        fields = ['id', 'user', 'role']


class BoardListSerializer(serializers.ModelSerializer):
    """Serializer for board list view."""
    owner = UserSerializer(read_only=True)
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Board
        fields = ['id', 'title', 'description', 'status', 'owner', 'members_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def get_members_count(self, obj):
        return obj.members.count()


class BoardCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating boards."""
    title = serializers.CharField(required=True)
    members = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Board
        fields = ['title', 'description', 'status', 'deadline', 'members']
        
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Board title cannot be empty")
        return value.strip()


class BoardDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed board view with all related data."""
    
    owner = UserSerializer(read_only=True)
    members = BoardMembershipSerializer(
        source="members", 
        many=True, 
        read_only=True
    )
    title = serializers.CharField(required=True)
    deadline = serializers.DateTimeField(required=False, allow_null=True)
    columns = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Board
        fields = [
            'id', 'title', 'description', 'status', 'owner', 'members', 
            'columns', 'deadline', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_columns(self, obj):
        try:
            from .column_serializers import ColumnSerializer
            columns = obj.columns.all().order_by('position')
            return ColumnSerializer(columns, many=True, context=self.context).data
        except Exception as e:
            logger.error(f"Error serializing columns for board {obj.id}: {str(e)}")
            return []

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Board title cannot be empty")
        return value.strip()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        try:
            memberships = BoardMembership.objects.filter(board=instance).select_related('user')
            members_data = []
            for membership in memberships:
                member_data = {
                    'id': membership.id,
                    'user': UserSerializer(membership.user).data,
                    'role': membership.role
                }
                members_data.append(member_data)
            data['members'] = members_data
        except Exception as e:
            logger.error(f"Error serializing members for board {instance.id}: {str(e)}")
            data['members'] = []
        
        logger.info(f"Board {instance.id} '{instance.title}' serialized with {len(data.get('columns', []))} columns and {len(data.get('members', []))} members")
        return data


class BoardSerializer(serializers.ModelSerializer):
    """General purpose board serializer."""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Board
        fields = ['id', 'title', 'description', 'status', 'owner', 'deadline', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
        
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Board title cannot be empty")
        return value.strip()