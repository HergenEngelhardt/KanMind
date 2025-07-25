from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User


class AuthResponseMixin:
    """Mixin for common authentication response building."""
    
    def _get_or_create_token(self, user):
        """Get or create authentication token for user.
        
        Args:
            user (User): Django user instance for which to get/create token
            
        Returns:
            Token: Authentication token instance for the user
        """
        token, created = Token.objects.get_or_create(user=user)
        return token

    def _build_user_data(self, user, token):
        """Build user data response with robust fullname handling.
        
        Args:
            user (User): Django user instance
            token (Token): Authentication token for the user
            
        Returns:
            dict: Dictionary containing user data with token, user_id, email, 
                  fullname, first_name, and last_name
        """
        fullname = self._generate_fullname(user)
        
        return {
            "token": token.key,
            "user_id": user.pk,
            "email": user.email,
            "fullname": fullname,
            "first_name": (user.first_name or "").strip(),
            "last_name": (user.last_name or "").strip(),
        }
    
    def _generate_fullname(self, user):
        """Generate fullname from user's first and last name with fallback.
        
        Args:
            user (User): Django user instance
            
        Returns:
            str: Generated fullname or fallback value
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
            return user.email.split('@')[0] if user.email else "User"


class GuestUserMixin:
    """Mixin for guest user functionality."""
    
    def _get_or_create_guest_user(self):
        """Get existing guest user or create new one if not found.
        
        Returns:
            User: Guest user instance
        """
        try:
            return User.objects.get(username="kevin@kovacsi.de")
        except User.DoesNotExist:
            return self._create_guest_user()

    def _create_guest_user(self):
        """Create a new guest user with predefined credentials.
        
        Returns:
            User: Newly created guest user instance
        """
        return User.objects.create_user(
            username="kevin@kovacsi.de",
            email="kevin@kovacsi.de",
            password="asdasdasd",
            first_name="Guest",
            last_name="User",
        )