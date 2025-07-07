from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .auth_utils import AuthResponseMixin, GuestUserMixin


class GuestLoginView(APIView, AuthResponseMixin, GuestUserMixin):
    """Guest login endpoint."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        guest_user = self._get_or_create_guest_user()
        token = self._get_or_create_token(guest_user)
        
        return Response(
            self._build_user_data(guest_user, token),
            status=status.HTTP_200_OK,
        )