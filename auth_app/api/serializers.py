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
    
    def _set_username_from_email(self, attrs):
        """
        Set username to email if username is not provided.
        
        Args:
            attrs (dict): Serializer attributes
            
        Returns:
            dict: Modified attributes with username set
        """
        if not attrs.get("username"):
            attrs["username"] = attrs.get("email")
        return attrs
    
    def _parse_full_name(self, attrs):
        """
        Parse full_name or fullname field into first_name and last_name.
        
        Args:
            attrs (dict): Serializer attributes
            
        Returns:
            dict: Modified attributes with first_name and last_name set
        """
        full_name_value = attrs.pop('full_name', None) or attrs.pop('fullname', None)
        
        if full_name_value:
            name_parts = full_name_value.split(' ', 1)
            attrs['first_name'] = name_parts[0]
            attrs['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        
        return attrs
    
    def validate(self, attrs):
        """
        Validate and process registration data.
        
        Args:
            attrs (dict): Serializer attributes
            
        Returns:
            dict: Validated and processed attributes
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        attrs = self._set_username_from_email(attrs)
        attrs = self._parse_full_name(attrs)
        return attrs
    
    def create(self, validated_data):
        """
        Create a new user with validated data.
        
        Args:
            validated_data (dict): Validated registration data
            
        Returns:
            User: Created user instance
            
        Raises:
            ValidationError: If user creation fails
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