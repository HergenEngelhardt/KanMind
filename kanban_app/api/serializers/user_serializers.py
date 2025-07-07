from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    fullname = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'fullname']
        
    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email