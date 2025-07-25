from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User


class EmailCheckView(APIView):
    """
    API view to check if a user exists by email and return user information.
    
    Provides endpoint to validate user existence and retrieve basic user data
    by email address.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handle GET request to check user existence by email.
        
        Args:
            request: HTTP request object containing email in query parameters
            
        Returns:
            Response: JSON response with user data or error message
            
        Raises:
            400: If email parameter is missing
            404: If user with given email does not exist
        """
        email = request.query_params.get('email')
        
        if not email:
            return self._email_missing_response()
        
        return self._get_user_by_email(email)

    def _email_missing_response(self):
        """
        Generate response for missing email parameter.
        
        Returns:
            Response: HTTP 400 response with error message
        """
        return Response(
            {"error": "Email parameter is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    def _get_user_by_email(self, email):
        """
        Retrieve user by email and return appropriate response.
        
        Args:
            email (str): Email address to search for
            
        Returns:
            Response: User data response or not found error
        """
        try:
            user = User.objects.get(email=email)
            return self._user_found_response(user)
        except User.DoesNotExist:
            return self._user_not_found_response()

    def _user_not_found_response(self):
        """
        Generate response for user not found.
        
        Returns:
            Response: HTTP 404 response with error message
        """
        return Response(
            {"error": "User not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

    def _user_found_response(self, user):
        """
        Generate response with user data when user is found.
        
        Args:
            user (User): Django User model instance
            
        Returns:
            Response: HTTP 200 response with user data dictionary
        """
        fullname = self._generate_fullname(user)
        user_data = self._build_user_data(user, fullname)
        
        return Response(user_data, status=status.HTTP_200_OK)

    def _generate_fullname(self, user):
        """
        Generate display name from user's first and last name or fallback.
        
        Args:
            user (User): Django User model instance
            
        Returns:
            str: Generated fullname or fallback to email/username
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

    def _build_user_data(self, user, fullname):
        """
        Build user data dictionary for API response.
        
        Args:
            user (User): Django User model instance
            fullname (str): Generated display name
            
        Returns:
            dict: Dictionary containing user information
        """
        return {
            "id": user.id,
            "email": user.email,
            "fullname": fullname,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }