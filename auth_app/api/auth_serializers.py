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
        """
        Validate authentication credentials.
        
        Args:
            attrs (dict): Dictionary containing email/username and password
            
        Returns:
            dict: Validated attributes with authenticated user
            
        Raises:
            serializers.ValidationError: If authentication fails
        """
        if self._is_guest_login(attrs):
            return self._handle_guest_login(attrs)
        
        self._validate_required_fields(attrs)
        username = self._get_username(attrs)
        user = self._authenticate_user(username, attrs.get("password"))
        
        attrs["user"] = user
        return attrs

    def _is_guest_login(self, attrs):
        """
        Check if provided credentials match guest login.
        
        Args:
            attrs (dict): Dictionary containing login credentials
            
        Returns:
            bool: True if guest credentials, False otherwise
        """
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password", "")
        
        guest_email = self._get_guest_email()
        guest_password = self._get_guest_password()
        
        return email == guest_email and password == guest_password

    def _handle_guest_login(self, attrs):
        """
        Handle guest user authentication.
        
        Args:
            attrs (dict): Dictionary containing login credentials
            
        Returns:
            dict: Validated attributes with guest user
        """
        guest_user = self._get_or_create_guest_user()
        attrs["user"] = guest_user
        return attrs

    def _validate_required_fields(self, attrs):
        """
        Validate that required fields are provided.
        
        Args:
            attrs (dict): Dictionary containing login credentials
            
        Raises:
            serializers.ValidationError: If required fields are missing
        """
        username = attrs.get("username")
        email = attrs.get("email")
        password = attrs.get("password")
        
        if (not username and not email) or not password:
            msg = "Either email or username and password must be provided."
            raise serializers.ValidationError(msg, code="authorization")

    def _get_username(self, attrs):
        """
        Get username from attributes, converting email if necessary.
        
        Args:
            attrs (dict): Dictionary containing login credentials
            
        Returns:
            str: Username for authentication
        """
        username = attrs.get("username")
        email = attrs.get("email")
        
        if email and not username:
            return self._get_username_from_email(email)
        return username

    def _authenticate_user(self, username, password):
        """
        Authenticate user with username and password.
        
        Args:
            username (str): Username for authentication
            password (str): Password for authentication
            
        Returns:
            User: Authenticated user object
            
        Raises:
            serializers.ValidationError: If authentication fails
        """
        user = authenticate(username=username, password=password)
        if not user:
            msg = "Unable to authenticate with provided credentials."
            raise serializers.ValidationError(msg, code="authorization")
        return user

    def _get_or_create_guest_user(self):
        """
        Get existing guest user or create new one.
        
        Returns:
            User: Guest user object
        """
        guest_email = self._get_guest_email()
        try:
            return User.objects.get(username=guest_email)
        except User.DoesNotExist:
            return self._create_guest_user()

    def _create_guest_user(self):
        """
        Create new guest user.
        
        Returns:
            User: Newly created guest user object
        """
        guest_email = self._get_guest_email()
        guest_password = self._get_guest_password()
        
        return User.objects.create_user(
            username=guest_email,
            email=guest_email,
            password=guest_password,
            first_name="Guest",
            last_name="User",
        )

    def _get_username_from_email(self, email):
        """
        Get username by looking up user with email address.
        
        Args:
            email (str): Email address to look up
            
        Returns:
            str: Username of user with given email
            
        Raises:
            serializers.ValidationError: If user with email does not exist
        """
        try:
            user = User.objects.get(email=email)
            return user.username
        except User.DoesNotExist:
            msg = "User with this email address does not exist."
            raise serializers.ValidationError(msg, code="authorization")

    def _get_guest_email(self):
        """
        Get guest email from settings.
        
        Returns:
            str: Guest email address
        """
        return getattr(settings, 'GUEST_EMAIL', 'kevin@kovacsi.de')

    def _get_guest_password(self):
        """
        Get guest password from settings.
        
        Returns:
            str: Guest password
        """