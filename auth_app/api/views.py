from .registration_views import RegisterView
from .login_views import LoginView
from .guest_views import GuestLoginView
from .auth_serializers import CustomAuthTokenSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

class EmailCheckView(APIView):
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        email = request.GET.get('email')
        if not email:
            return Response({'error': 'Email parameter required'}, status=400)
        
        try:
            user = User.objects.get(email=email)
            first_name = (user.first_name or "").strip()
            last_name = (user.last_name or "").strip()
            
            if first_name and last_name:
                fullname = f"{first_name} {last_name}"
            elif first_name:
                fullname = first_name
            elif last_name:
                fullname = last_name
            else:
                fullname = user.email.split('@')[0] if user.email else user.username
            
            return Response({
                'id': user.id,
                'email': user.email,
                'fullname': fullname,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            })
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

def login_view(request):
    view = LoginView.as_view()
    return view(request)

def registration_view(request):
    view = RegisterView.as_view()
    return view(request)

def email_check(request):
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