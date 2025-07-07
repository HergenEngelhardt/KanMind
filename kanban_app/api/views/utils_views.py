from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from kanban_app.api.serializers.user_serializers import UserSerializer


class EmailCheckView(APIView):
    """Check if user exists by email address."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = request.query_params.get("email")

        if not email:
            return Response(
                {"error": "Email parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            return self._user_found_response(user)
        except User.DoesNotExist:
            return Response({"exists": False}, status=status.HTTP_200_OK)

    def _user_found_response(self, user):
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
        
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "fullname": fullname,
                "exists": True
            },
            status=status.HTTP_200_OK,
        )


class TaskReorderView(APIView):
    """Reorder tasks within or between columns."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"message": "Task reordering not implemented yet"})