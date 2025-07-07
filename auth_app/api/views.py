import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from .serializers import RegisterSerializer, UserSerializer

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
            attrs (dict): Authentication attributes
            
        Returns:
            dict: Validated attributes with user instance
        """
        if self._is_guest_login(attrs):
            return self._handle_guest_login(attrs)
        
        self._validate_required_fields(attrs)
        username = self._get_username(attrs)
        user = self._authenticate_user(username, attrs.get("password"))
        
        attrs["user"] = user
        return attrs

    def _is_guest_login(self, attrs):
        """Check if this is a guest login attempt with better security."""
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password", "")
        
        guest_email = getattr(settings, 'GUEST_EMAIL', 'kevin@kovacsi.de')
        guest_password = getattr(settings, 'GUEST_PASSWORD', 'asdasdasd')
        
        return email == guest_email and password == guest_password

    def _handle_guest_login(self, attrs):
        """Handle guest login authentication."""
        guest_user = self._get_or_create_guest_user()
        attrs["user"] = guest_user
        return attrs

    def _validate_required_fields(self, attrs):
        """Validate required authentication fields."""
        username = attrs.get("username")
        email = attrs.get("email")
        password = attrs.get("password")
        
        if (not username and not email) or not password:
            msg = "Either email or username and password must be provided."
            raise serializers.ValidationError(msg, code="authorization")

    def _get_username(self, attrs):
        """Get username from attrs, converting email if needed."""
        username = attrs.get("username")
        email = attrs.get("email")
        
        if email and not username:
            return self._get_username_from_email(email)
        return username

    def _authenticate_user(self, username, password):
        """Authenticate user with username and password."""
        user = authenticate(username=username, password=password)
        if not user:
            msg = "Unable to authenticate with provided credentials."
            raise serializers.ValidationError(msg, code="authorization")
        return user

    def _get_or_create_guest_user(self):
        """
        Get or create guest user for demo purposes.
        
        Returns:
            User: Guest user instance
        """
        try:
            return User.objects.get(username="guest@example.com")
        except User.DoesNotExist:
            return self._create_guest_user()

    def _create_guest_user(self):
        """Create new guest user."""
        return User.objects.create_user(
            username="guest@example.com",
            email="guest@example.com",
            password="guest1234",
            first_name="Guest",
            last_name="User",
        )

    def _get_username_from_email(self, email):
        """
        Get username from email address.
        
        Args:
            email (str): Email address
            
        Returns:
            str: Username corresponding to email
            
        Raises:
            ValidationError: If user with email doesn't exist
        """
        try:
            user = User.objects.get(email=email)
            return user.username
        except User.DoesNotExist:
            msg = "User with this email address does not exist."
            raise serializers.ValidationError(msg, code="authorization")


class RegisterView(APIView):
    """
    User registration endpoint.
    
    Creates new user account and returns authentication token.
    Accessible without authentication.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Register new user.
        
        Args:
            request: HTTP request with registration data
            
        Returns:
            Response: User data with authentication token or validation errors
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            return self._create_user_response(serializer)
        return self._validation_error_response(serializer)

    def _create_user_response(self, serializer):
        """Create user and return success response."""
        user = serializer.save()
        token = self._get_or_create_token(user)
        
        return Response(
            self._build_user_data(user, token),
            status=status.HTTP_201_CREATED,
        )

    def _validation_error_response(self, serializer):
        """Return validation error response."""
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )

    def _get_or_create_token(self, user):
        """Get or create authentication token for user."""
        token, created = Token.objects.get_or_create(user=user)
        return token

    def _build_user_data(self, user, token):
        """Build user data response with robust fullname handling."""
        first_name = (user.first_name or "").strip()
        last_name = (user.last_name or "").strip()
        
        if first_name and last_name:
            fullname = f"{first_name} {last_name}"
        elif first_name:
            fullname = first_name
        elif last_name:
            fullname = last_name
        else:
            fullname = user.email.split('@')[0] if user.email else "User"
        
        return {
            "token": token.key,
            "user_id": user.pk,
            "email": user.email,
            "fullname": fullname,
            "first_name": first_name,
            "last_name": last_name,
        }

class LoginView(ObtainAuthToken):
    """
    User login endpoint.
    
    Authenticates user and returns authentication token.
    Supports both email and username authentication.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        """Authenticate user and return token with improved error handling."""
        try:
            serializer = self._get_validated_serializer(request)
            user = serializer.validated_data["user"]
            token = self._get_or_create_token(user)
            
            return Response(self._build_user_data(user, token))
            
        except ValidationError as e:
            return Response(
                {"error": "Invalid credentials provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Login failed due to server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_validated_serializer(self, request):
        """Get and validate serializer."""
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return serializer

    def _get_or_create_token(self, user):
        """Get or create authentication token for user."""
        token, created = Token.objects.get_or_create(user=user)
        return token

    def _build_user_data(self, user, token):
        """Build user data response with robust fullname handling."""
        first_name = (user.first_name or "").strip()
        last_name = (user.last_name or "").strip()
        
        if first_name and last_name:
            fullname = f"{first_name} {last_name}"
        elif first_name:
            fullname = first_name
        elif last_name:
            fullname = last_name
        else:
            fullname = user.email.split('@')[0] if user.email else "User"
        
        return {
            "token": token.key,
            "user_id": user.pk,
            "email": user.email,
            "fullname": fullname,
            "first_name": first_name,
            "last_name": last_name,
        }

class GuestLoginView(APIView):
    """
    Guest login endpoint.
    
    Creates or authenticates guest user for demo purposes.
    Accessible without authentication.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Create or authenticate guest user.
        
        Args:
            request: HTTP request (no data required)
            
        Returns:
            Response: Guest user data with authentication token
        """
        guest_user = self._get_or_create_guest_user()
        token = self._get_or_create_token(guest_user)
        
        return Response(
            self._build_user_data(guest_user, token),
            status=status.HTTP_200_OK,
        )

    def _get_or_create_guest_user(self):
        """
        Get or create guest user for demo purposes.
        
        Returns:
            User: Guest user instance
        """
        try:
            return User.objects.get(username="guest@example.com")
        except User.DoesNotExist:
            return self._create_guest_user()

    def _create_guest_user(self):
        """Create new guest user."""
        return User.objects.create_user(
            username="guest@example.com",
            email="guest@example.com",
            password="guest1234",
            first_name="Guest",
            last_name="User",
        )

    def _get_or_create_token(self, user):
        """Get or create authentication token for user."""
        token, created = Token.objects.get_or_create(user=user)
        return token

    def _build_user_data(self, user, token):
        """Build user data response with robust fullname handling."""
        first_name = (user.first_name or "").strip()
        last_name = (user.last_name or "").strip()
        
        if first_name and last_name:
            fullname = f"{first_name} {last_name}"
        elif first_name:
            fullname = first_name
        elif last_name:
            fullname = last_name
        else:
            fullname = user.email.split('@')[0] if user.email else "User"
        
        return {
            "token": token.key,
            "user_id": user.pk,
            "email": user.email,
            "fullname": fullname,
            "first_name": first_name,
            "last_name": last_name,
        }