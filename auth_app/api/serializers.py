from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "fullname")

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class RegisterSerializer(serializers.ModelSerializer):
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
        if not attrs.get("username"):
            attrs["username"] = attrs.get("email")
        return attrs
    
    def _parse_full_name(self, attrs):
        full_name = attrs.get('full_name') or attrs.get('fullname')
        if full_name and not (attrs.get('first_name') or attrs.get('last_name')):
            parts = full_name.strip().split(' ', 1)
            attrs['first_name'] = parts[0]
            if len(parts) > 1:
                attrs['last_name'] = parts[1]
        return attrs
    
    def validate(self, attrs):
        attrs = self._set_username_from_email(attrs)
        attrs = self._parse_full_name(attrs)
        
        if User.objects.filter(email=attrs.get('email')).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('full_name', None)
        validated_data.pop('fullname', None)
        
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


UserRegistrationSerializer = RegisterSerializer