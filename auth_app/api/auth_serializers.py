from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings


class CustomAuthTokenSerializer(serializers.Serializer):
    """
    Custom authentication token serializer.
    
    Supports authentication with either email or username.
    Includes special handling for guest login credentials.
    """
    
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        if self._is_guest_login(attrs):
            return self._handle_guest_login(attrs)
        
        self._validate_required_fields(attrs)
        username = self._get_username(attrs)
        user = self._authenticate_user(username, attrs.get("password"))
        
        attrs["user"] = user
        return attrs

    def _is_guest_login(self, attrs):
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password", "")
        
        guest_email = getattr(settings, 'GUEST_EMAIL', 'kevin@kovacsi.de')
        guest_password = getattr(settings, 'GUEST_PASSWORD', 'asdasdasd')
        
        return email == guest_email and password == guest_password

    def _handle_guest_login(self, attrs):
        guest_user = self._get_or_create_guest_user()
        attrs["user"] = guest_user
        return attrs

    def _validate_required_fields(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email")
        password = attrs.get("password")
        
        if (not username and not email) or not password:
            msg = "Either email or username and password must be provided."
            raise serializers.ValidationError(msg, code="authorization")

    def _get_username(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email")
        
        if email and not username:
            return self._get_username_from_email(email)
        return username

    def _authenticate_user(self, username, password):
        user = authenticate(username=username, password=password)
        if not user:
            msg = "Unable to authenticate with provided credentials."
            raise serializers.ValidationError(msg, code="authorization")
        return user

    def _get_or_create_guest_user(self):
        guest_email = getattr(settings, 'GUEST_EMAIL', 'kevin@kovacsi.de')
        try:
            return User.objects.get(username=guest_email)
        except User.DoesNotExist:
            return self._create_guest_user()

    def _create_guest_user(self):
        guest_email = getattr(settings, 'GUEST_EMAIL', 'kevin@kovacsi.de')
        guest_password = getattr(settings, 'GUEST_PASSWORD', 'asdasdasd')
        return User.objects.create_user(
            username=guest_email,
            email=guest_email,
            password=guest_password,
            first_name="Guest",
            last_name="User",
    )

    def _get_username_from_email(self, email):
        try:
            user = User.objects.get(email=email)
            return user.username
        except User.DoesNotExist:
            msg = "User with this email address does not exist."
            raise serializers.ValidationError(msg, code="authorization")