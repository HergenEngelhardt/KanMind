from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer
from .auth_utils import AuthResponseMixin


class RegisterView(APIView, AuthResponseMixin):
    """
    User registration endpoint.
    
    Handles user registration requests and returns user data with authentication token.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request for user registration.
        
        Args:
            request: HTTP request object containing user registration data
            
        Returns:
            Response: JSON response with user data and token on success,
                     or validation errors on failure
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            return self._create_user_response(serializer)
        return self._validation_error_response(serializer)

    def _create_user_response(self, serializer):
        """
        Create successful user registration response.
        
        Args:
            serializer (RegisterSerializer): Validated serializer instance
            
        Returns:
            Response: HTTP 201 response with user data and authentication token
        """
        user = serializer.save()
        token = self._get_or_create_token(user)
        
        return Response(
            self._build_user_data(user, token),
            status=status.HTTP_201_CREATED,
        )

    def _validation_error_response(self, serializer):
        """
        Create validation error response.
        
        Args:
            serializer (RegisterSerializer): Invalid serializer instance with errors
            
        Returns:
            Response: HTTP 400 response with validation error details
        """
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )