"""
Serializers for Column objects in the Kanban app.
"""
from rest_framework import serializers
from django.core.cache import cache
import logging

from kanban_app.models import Column

logger = logging.getLogger(__name__)


class ColumnSerializer(serializers.ModelSerializer):
    """
    Serializer for Column model.
    
    Processes reading and creating column data.
    
    Args:
        serializers.ModelSerializer: DRF base serializer class
    """
    class Meta:
        model = Column
        fields = ('id', 'name', 'board', 'position')
        read_only_fields = ('board', 'position')