from django.urls import path
from .views import RegisterView, LoginView, GuestLoginView

urlpatterns = [
    path("registration/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("guest-login/", GuestLoginView.as_view(), name="guest-login"),
]
