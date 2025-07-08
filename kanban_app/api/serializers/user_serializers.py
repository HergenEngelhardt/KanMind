from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    
    Provides user information for API responses.
    Includes calculated fullname field.
    """
    
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "username", "fullname"]
        read_only_fields = ["id"]

    def get_fullname(self, obj):
        """Return user's full name."""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username