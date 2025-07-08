from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model representation.
    
    Used for displaying user information in API responses.
    Includes basic user fields without sensitive data.
    """
    
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Handles user creation with email as primary identifier.
    Supports both separate first_name/last_name fields and combined full_name.
    Automatically sets username to email if not provided.
    """
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    full_name = serializers.CharField(required=False, write_only=True)
    fullname = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'full_name', 'fullname', 'username']
        extra_kwargs = {
            'username': {'required': False},
        }
    
    def validate(self, attrs):
        """
        Validate and process registration data.
        
        Sets username to email if not provided.
        Splits full_name into first_name and last_name if provided.
        
        Args:
            attrs (dict): Serializer attributes
            
        Returns:
            dict: Validated and processed attributes
        """
        if not attrs.get("username"):
            attrs["username"] = attrs.get("email")
        
        full_name_value = attrs.pop('full_name', None) or attrs.pop('fullname', None)
    
        if full_name_value:
            name_parts = full_name_value.split(' ', 1)
            attrs['first_name'] = name_parts[0]
            attrs['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        
        return attrs
    
    def create(self, validated_data):
        """
        Create a new user with validated data.
        
        Args:
            validated_data (dict): Validated registration data
            
        Returns:
            User: Created user instance
        """
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user