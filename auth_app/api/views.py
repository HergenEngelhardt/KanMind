from .registration_views import RegisterView
from .login_views import LoginView
from .guest_views import GuestLoginView
from .auth_serializers import CustomAuthTokenSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User


class EmailCheckView(APIView):
    """
    API view for checking if an email exists and retrieving user information.
    """
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        """
        Handle GET request to check email existence and return user data.
        
        Args:
            request: HTTP request object containing email parameter
            
        Returns:
            Response: JSON response with user data or error message
            
        Raises:
            ValidationError: If email parameter is missing
        """
        email = request.GET.get('email')
        if not email:
            return Response({'error': 'Email parameter required'}, status=400)
        
        try:
            user = User.objects.get(email=email)
            user_data = self._build_user_response(user)
            return Response(user_data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
    
    def _build_user_response(self, user):
        """
        Build user response data dictionary.
        
        Args:
            user (User): Django User model instance
            
        Returns:
            dict: Dictionary containing user information
        """
        fullname = self._get_user_fullname(user)
        return {
            'id': user.id,
            'email': user.email,
            'fullname': fullname,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
    
    def _get_user_fullname(self, user):
        """
        Generate full name from user first and last name.
        
        Args:
            user (User): Django User model instance
            
        Returns:
            str: User's full name or fallback identifier
        """
        first_name = (user.first_name or "").strip()
        last_name = (user.last_name or "").strip()
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return user.email.split('@')[0] if user.email else user.username


def login_view(request):
    """
    Function-based view wrapper for LoginView.
    
    Args:
        request: HTTP request object
        
    Returns:
        Response: Login view response
    """
    view = LoginView.as_view()
    return view(request)


def registration_view(request):
    """
    Function-based view wrapper for RegisterView.
    
    Args:
        request: HTTP request object
        
    Returns:
        Response: Registration view response
    """
    view = RegisterView.as_view()
    return view(request)


def email_check(request):
    """
    Function-based view wrapper for EmailCheckView.
    
    Args:
        request: HTTP request object
        
    Returns:
        Response: Email check view response
    """
    view = EmailCheckView.as_view()
    return view(request)


__all__ = [
    'RegisterView',
    'LoginView', 
    'GuestLoginView',
    'CustomAuthTokenSerializer',
    'EmailCheckView',
    'login_view',
    'registration_view',
    'email_check'
]