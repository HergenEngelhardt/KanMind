from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from auth_app.api.serializers import RegisterSerializer, CustomAuthTokenSerializer


class RegisterSerializerTest(TestCase):
    """Test RegisterSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='existingpass123'
        )
    
    def test_valid_registration_data(self):
        """Test serializer with valid registration data."""
        data = {
            'email': 'new@example.com',
            'password': 'ValidPass123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['email'], 'new@example.com')
    
    def test_email_as_username(self):
        """Test email is used as username when not provided."""
        data = {
            'email': 'new@example.com',
            'password': 'ValidPass123!'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['username'], 'new@example.com')
    
    def test_full_name_splitting(self):
        """Test full_name is split correctly."""
        data = {
            'email': 'new@example.com',
            'password': 'ValidPass123!',
            'full_name': 'John Doe Smith'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['first_name'], 'John')
        self.assertEqual(serializer.validated_data['last_name'], 'Doe Smith')
    
    def test_full_name_single_name(self):
        """Test full_name with single name."""
        data = {
            'email': 'new@example.com',
            'password': 'ValidPass123!',
            'full_name': 'John'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['first_name'], 'John')
        self.assertEqual(serializer.validated_data['last_name'], '')
    
    def test_invalid_email(self):
        """Test validation fails for invalid email."""
        data = {
            'email': 'invalid-email',
            'password': 'ValidPass123!'
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_weak_password(self):
        """Test validation fails for weak password."""
        data = {
            'email': 'new@example.com',
            'password': '123'
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_user_creation(self):
        """Test user is created correctly."""
        data = {
            'email': 'create@example.com',
            'password': 'ValidPass123!',
            'first_name': 'Create',
            'last_name': 'Test'
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertEqual(user.email, 'create@example.com')
        self.assertEqual(user.username, 'create@example.com')
        self.assertEqual(user.first_name, 'Create')
        self.assertEqual(user.last_name, 'Test')
        self.assertTrue(user.check_password('ValidPass123!'))


class CustomAuthTokenSerializerTest(TestCase):
    """Test CustomAuthTokenSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_email_authentication(self):
        """Test authentication with email."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        serializer = CustomAuthTokenSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)
    
    def test_username_authentication(self):
        """Test authentication with username."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        serializer = CustomAuthTokenSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)
    
    def test_guest_authentication(self):
        """Test guest authentication."""
        data = {
            'email': 'kevin@kovacsi.de',
            'password': 'asdasdasd'
        }
        serializer = CustomAuthTokenSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'].username, 'guest@example.com')
        self.assertEqual(serializer.validated_data['user'].email, 'guest@example.com')
    
    def test_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        serializer = CustomAuthTokenSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_nonexistent_email(self):
        """Test authentication with non-existent email."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        }
        serializer = CustomAuthTokenSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_missing_credentials(self):
        """Test validation with missing credentials."""
        data = {
            'password': 'testpass123'
        }
        serializer = CustomAuthTokenSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_missing_password(self):
        """Test validation with missing password."""
        data = {
            'email': 'test@example.com'
        }
        serializer = CustomAuthTokenSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_guest_user_creation(self):
        """Test guest user is created when doesn't exist."""
        User.objects.filter(username='guest@example.com').delete()
        
        data = {
            'email': 'kevin@kovacsi.de',
            'password': 'asdasdasd'
        }
        serializer = CustomAuthTokenSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        guest_user = serializer.validated_data['user']
        self.assertEqual(guest_user.username, 'guest@example.com')
        self.assertEqual(guest_user.first_name, 'Guest')
        self.assertEqual(guest_user.last_name, 'User')


class AuthAPIEndpointsTest(APITestCase):
    """Test authentication API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.register_url = '/api/auth/registration/'
        self.login_url = '/api/auth/login/'
        self.guest_login_url = '/api/auth/guest-login/'
    
    def test_user_registration_success(self):
        """Test successful user registration."""
        data = {
            'email': 'new@example.com',
            'password': 'ValidPass123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        self.assertEqual(response.data['email'], 'new@example.com')
        self.assertEqual(response.data['fullname'], 'New User')
        
        user = User.objects.get(email='new@example.com')
        self.assertEqual(user.username, 'new@example.com')
    
    def test_user_registration_with_full_name(self):
        """Test registration with full_name field."""
        data = {
            'email': 'fullname@example.com',
            'password': 'ValidPass123!',
            'full_name': 'John Doe Smith'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['fullname'], 'John Doe Smith')
        
        user = User.objects.get(email='fullname@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe Smith')
    
    def test_user_registration_invalid_data(self):
        """Test registration with invalid data."""
        data = {
            'email': 'invalid-email',
            'password': 'short'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
    
    def test_user_registration_missing_email(self):
        """Test registration without email."""
        data = {
            'password': 'ValidPass123!'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_user_login_with_email_success(self):
        """Test successful user login with email."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['fullname'], 'Test User')
    
    def test_user_login_with_username_success(self):
        """Test successful user login with username."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user_id'], self.user.id)
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_user_login_nonexistent_email(self):
        """Test login with non-existent email."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_user_login_missing_credentials(self):
        """Test login with missing credentials."""
        data = {
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_guest_login_success(self):
        """Test guest login endpoint."""
        response = self.client.post(self.guest_login_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['email'], 'guest@example.com')
        self.assertEqual(response.data['fullname'], 'Guest User')
        
        guest_user = User.objects.get(username='guest@example.com')
        self.assertEqual(guest_user.email, 'guest@example.com')
    
    def test_guest_login_existing_user(self):
        """Test guest login when guest user already exists."""
        guest_user = User.objects.create_user(
            username='guest@example.com',
            email='guest@example.com',
            password='guest1234',
            first_name='Guest',
            last_name='User'
        )
        
        response = self.client.post(self.guest_login_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], guest_user.id)
    
    def test_special_guest_login_credentials(self):
        """Test special guest login credentials in login endpoint."""
        data = {
            'email': 'kevin@kovacsi.de',
            'password': 'asdasdasd'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['email'], 'guest@example.com')
    
    def test_token_creation_on_registration(self):
        """Test that token is created on registration."""
        data = {
            'email': 'token@example.com',
            'password': 'ValidPass123!'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email='token@example.com')
        token = Token.objects.get(user=user)
        self.assertEqual(response.data['token'], token.key)
    
    def test_token_creation_on_login(self):
        """Test that token is created/retrieved on login."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        token = Token.objects.get(user=self.user)
        self.assertEqual(response.data['token'], token.key)
    
    def test_response_format_consistency(self):
        """Test that all endpoints return consistent response format."""
        reg_data = {
            'email': 'format@example.com',
            'password': 'ValidPass123!',
            'first_name': 'Format',
            'last_name': 'Test'
        }
        reg_response = self.client.post(self.register_url, reg_data)
        
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data)
        
        guest_response = self.client.post(self.guest_login_url)
        
        for response in [reg_response, login_response, guest_response]:
            self.assertIn('token', response.data)
            self.assertIn('user_id', response.data)
            self.assertIn('email', response.data)
            self.assertIn('fullname', response.data)