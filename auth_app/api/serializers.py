from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    full_name = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'full_name', 'username']
        extra_kwargs = {
            'username': {'required': False},
        }
    
    def validate(self, attrs):
        if not attrs.get("username"):
            attrs["username"] = attrs.get("email")
            
        if 'full_name' in attrs:
            full_name = attrs.pop('full_name')
            name_parts = full_name.split(' ', 1)
            attrs['first_name'] = name_parts[0]
            attrs['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
            
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user