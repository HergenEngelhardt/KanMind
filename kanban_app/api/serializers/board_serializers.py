"""
Serializers for Board objects in the Kanban app.

Contains serializers for boards, board details and board memberships.
"""
from rest_framework import serializers
from django.contrib.auth.models import User

from kanban_app.models import Board, BoardMembership
from .user_serializers import UserSerializer


class BoardMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for BoardMembership model.
    
    Handles the relationship between users and boards with role information
    and provides user details through nested serialization.
    
    Args:
        serializers.ModelSerializer: DRF base serializer class
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BoardMembership
        fields = ['id', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class BoardSerializer(serializers.ModelSerializer):
    """
    Serializer for board creation and listing.
    
    Provides basic board information and owner data.
    
    Args:
        serializers.ModelSerializer: DRF base serializer class
    """
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Board
        fields = ('id', 'name', 'description', 'owner', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class BoardDetailSerializer(BoardSerializer):
    """
    Extended serializer for detailed board information.
    
    Includes additional member and column information.
    
    Args:
        BoardSerializer: Base serializer for board data
    """
    members = serializers.SerializerMethodField()
    columns = serializers.SerializerMethodField()
    
    class Meta(BoardSerializer.Meta):
        fields = BoardSerializer.Meta.fields + ('members', 'columns')

    def get_members(self, obj):
        """
        Format member information with roles.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            list: List of member dictionaries with user info and roles
        """
        try:
            memberships = obj.boardmembership_set.all().select_related('user')
            return [self._format_membership(m) for m in memberships]
        except Exception:
            return []
            
    def _format_membership(self, membership):
        """
        Format a single membership.
        
        Args:
            membership (BoardMembership): Membership object
            
        Returns:
            dict: Formatted membership data
        """
        return {
            'id': membership.id,
            'user': UserSerializer(membership.user).data,
            'role': membership.role
        }

    def get_columns(self, obj):
        """
        Get and format the columns of the board.
        
        Args:
            obj (Board): Board instance
            
        Returns:
            list: List of formatted column data
        """
        from .column_serializers import ColumnSerializer
        columns = obj.columns.all().order_by('position')
        return ColumnSerializer(columns, many=True).data