from rest_framework import serializers
from kanban_app.models import Board, BoardMembership, Column
from .user_serializers import UserSerializer
import logging

logger = logging.getLogger(__name__)


class BoardMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = BoardMembership
        fields = ['id', 'user', 'role']


class ColumnBasicSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Column
        fields = ['id', 'title', 'position']


class BoardListSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    title = serializers.CharField(required=False)
    deadline = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = Board
        fields = [
            'id', 'title', 'description', 'status', 'deadline', 
            'owner', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        if not data.get('title', '').strip():
            raise serializers.ValidationError("Board title is required")
        return data
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        logger.info(f"BoardListSerializer output keys: {data.keys()}")
        return data


class BoardDetailSerializer(serializers.ModelSerializer):
    
    owner = UserSerializer(read_only=True)
    members = BoardMembershipSerializer(
        source="boardmembership_set", 
        many=True, 
        read_only=True
    )
    title = serializers.CharField(required=False)
    deadline = serializers.DateTimeField(required=False, allow_null=True)
    columns = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Board
        fields = [
            'id', 'title', 'description', 'status', 'deadline',
            'owner', 'members', 'columns', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def get_columns(self, obj):
        try:
            columns = Column.objects.filter(board=obj).order_by('position')
            logger.info(f"Loading {columns.count()} columns for board {obj.id}")
            
            if columns.count() == 0:
                logger.warning(f"Board {obj.id} has no columns!")
                return []
            
            serialized_columns = ColumnBasicSerializer(columns, many=True).data
            logger.info(f"Serialized columns: {len(serialized_columns)}")
            
            return serialized_columns
        except Exception as e:
            logger.error(f"Error serializing columns: {str(e)}")
            return []
    
    def get_members_debug_info(self, obj):
        """Debug method to analyze the members data."""
        try:
            memberships = BoardMembership.objects.filter(board=obj)
            logger.info(f"Found {memberships.count()} memberships for board {obj.id}")
            
            for m in memberships:
                logger.info(f"Membership ID: {m.id}, User: {m.user.username}, Role: {m.role}")
            
            return memberships
        except Exception as e:
            logger.error(f"Error retrieving memberships: {str(e)}")
            return []

    def validate(self, data):
        if not data.get('title', '').strip():
            raise serializers.ValidationError("Board title is required")
        return data
    
    def to_representation(self, instance):
        try:
            data = super().to_representation(instance)
            columns = self.get_columns(instance)
            data['columns'] = columns
            
            # Debug members data
            self.get_members_debug_info(instance)  
            logger.info(f"BoardDetailSerializer members count: {len(data.get('members', []))}")
            logger.info(f"BoardDetailSerializer members data: {data.get('members', [])}")
            
            logger.info(f"BoardDetailSerializer output keys: {data.keys()}")
            logger.info(f"BoardDetailSerializer title: {data.get('title', 'NO TITLE FOUND')}")
            logger.info(f"Final board representation - ID: {instance.id}, Columns: {len(columns)}")
            return data
            
        except Exception as e:
            logger.error(f"Board serialization error: {str(e)}")
            # Try to include members even in error case
            try:
                members = list(BoardMembership.objects.filter(board=instance))
                members_data = BoardMembershipSerializer(members, many=True).data
            except:
                members_data = []
                
            return {
                'id': getattr(instance, 'id', None),
                'title': getattr(instance, 'title', ''),
                'description': getattr(instance, 'description', ''),
                'status': getattr(instance, 'status', 'PLANNING'),
                'deadline': None,
                'owner': None,
                'members': members_data,
                'columns': [],  
                'created_at': None,
                'updated_at': None
            }