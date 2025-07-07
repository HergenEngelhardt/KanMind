from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User


class AuthResponseMixin:
    """Mixin for common authentication response building."""
    
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


class GuestUserMixin:
    """Mixin for guest user functionality."""
    
    def _get_or_create_guest_user(self):
        try:
            return User.objects.get(username="guest@example.com")
        except User.DoesNotExist:
            return self._create_guest_user()

    def _create_guest_user(self):
        return User.objects.create_user(
            username="guest@example.com",
            email="guest@example.com",
            password="guest1234",
            first_name="Guest",
            last_name="User",
        )