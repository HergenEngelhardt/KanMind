from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with password confirmation.
    
    Args:
        fullname: User's full name as a single string
        email: User's email address
        password: User's password
        repeated_password: Password confirmation
    """
    fullname = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    repeated_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    def validate_email(self, value):
        """
        Check that the email is not already in use.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ein Benutzer mit dieser E-Mail existiert bereits.")
        return value
        
    class Meta:
        model = User
        fields = ['email', 'fullname', 'password', 'repeated_password']
        
    def validate(self, attrs):
        """
        Validates that passwords match.
        
        Args:
            attrs: Serializer attributes
            
        Returns:
            dict: Validated attributes
            
        Raises:
            ValidationError: If passwords don't match
        """
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """
        Creates a new user with validated data.
        
        Args:
            validated_data: Validated form data
            
        Returns:
            User: New user instance
        """
        validated_data.pop('repeated_password')
        fullname = validated_data.pop('fullname')
        
        name_parts = fullname.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        return User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name
        )