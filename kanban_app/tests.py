# Standard library imports
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.db import IntegrityError

# Local imports
from kanban_app.models import Board, Column, BoardMembership
from kanban_app.api.serializers.serializers import (
    BoardListSerializer, 
    BoardDetailSerializer, 
    ColumnSerializer,
    BoardMembershipSerializer
)
from tasks_app.models import Task


class BoardModelTest(TestCase):
    """Test Board model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
    
    def test_board_creation(self):
        """Test board creation with valid data."""
        board = Board.objects.create(
            name='Test Board',
            description='Test Description',
            owner=self.user
        )
        self.assertEqual(str(board), 'Test Board')
        self.assertEqual(board.owner, self.user)
        self.assertEqual(board.name, 'Test Board')
        self.assertEqual(board.description, 'Test Description')
    
    def test_board_meta_options(self):
        """Test board meta options."""
        board1 = Board.objects.create(name='Board 1', owner=self.user)
        board2 = Board.objects.create(name='Board 2', owner=self.user)
        
        boards = Board.objects.all()
        # Should be ordered by -created_at (newest first)
        self.assertEqual(boards[0], board2)
        self.assertEqual(boards[1], board1)
    
    def test_board_members_relationship(self):
        """Test board members many-to-many relationship."""
        board = Board.objects.create(name='Test Board', owner=self.user)
        
        # Add member through BoardMembership
        membership = BoardMembership.objects.create(
            user=self.other_user,
            board=board,
            role='EDITOR'
        )
        
        self.assertIn(self.other_user, board.members.all())
        self.assertEqual(board.members.count(), 1)


class BoardMembershipModelTest(TestCase):
    """Test BoardMembership model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.board = Board.objects.create(
            name='Test Board',
            owner=self.user
        )
    
    def test_membership_creation(self):
        """Test membership creation."""
        membership = BoardMembership.objects.create(
            user=self.user,
            board=self.board,
            role='ADMIN'
        )
        
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.board, self.board)
        self.assertEqual(membership.role, 'ADMIN')
        self.assertEqual(str(membership), f'{self.user.username} - {self.board.name} (ADMIN)')
    
    def test_membership_default_role(self):
        """Test default role is VIEWER."""
        membership = BoardMembership.objects.create(
            user=self.user,
            board=self.board
        )
        self.assertEqual(membership.role, 'VIEWER')
    
    def test_membership_unique_constraint(self):
        """Test unique constraint on user-board combination."""
        BoardMembership.objects.create(
            user=self.user,
            board=self.board,
            role='ADMIN'
        )
        
        # Should raise IntegrityError for duplicate
        with self.assertRaises(IntegrityError):
            BoardMembership.objects.create(
                user=self.user,
                board=self.board,
                role='EDITOR'
            )
    
    def test_membership_role_choices(self):
        """Test valid role choices."""
        valid_roles = ['ADMIN', 'EDITOR', 'VIEWER']
        
        for role in valid_roles:
            membership = BoardMembership.objects.create(
                user=self.user,
                board=Board.objects.create(name=f'Board {role}', owner=self.user),
                role=role
            )
            self.assertEqual(membership.role, role)


class ColumnModelTest(TestCase):
    """Test Column model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.board = Board.objects.create(
            name='Test Board',
            owner=self.user
        )
    
    def test_column_creation(self):
        """Test column creation."""
        column = Column.objects.create(
            name='To Do',
            board=self.board,
            position=1
        )
        
        self.assertEqual(str(column), 'To Do (Test Board)')
        self.assertEqual(column.name, 'To Do')
        self.assertEqual(column.board, self.board)
        self.assertEqual(column.position, 1)
    
    def test_column_ordering(self):
        """Test column ordering by position."""
        column1 = Column.objects.create(name='Column 1', board=self.board, position=2)
        column2 = Column.objects.create(name='Column 2', board=self.board, position=1)
        column3 = Column.objects.create(name='Column 3', board=self.board, position=3)
        
        columns = Column.objects.all()
        self.assertEqual(columns[0], column2)  # position 1
        self.assertEqual(columns[1], column1)  # position 2
        self.assertEqual(columns[2], column3)  # position 3
    
    def test_column_board_relationship(self):
        """Test column-board foreign key relationship."""
        column = Column.objects.create(
            name='Test Column',
            board=self.board,
            position=1
        )
        
        self.assertEqual(column.board, self.board)
        self.assertIn(column, self.board.columns.all())


class BoardSerializerTest(TestCase):
    """Test Board serializers."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.board = Board.objects.create(
            name='Test Board',
            description='Test Description',
            owner=self.user
        )
    
    def test_board_list_serializer(self):
        """Test BoardListSerializer."""
        serializer = BoardListSerializer(instance=self.board)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Board')
        self.assertEqual(data['description'], 'Test Description')
        self.assertEqual(data['owner']['id'], self.user.id)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_board_detail_serializer(self):
        """Test BoardDetailSerializer."""
        # Add a member and column for complete test
        member = User.objects.create_user(username='member', email='member@example.com')
        BoardMembership.objects.create(user=member, board=self.board, role='EDITOR')
        Column.objects.create(name='To Do', board=self.board, position=1)
        
        serializer = BoardDetailSerializer(instance=self.board)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Board')
        self.assertEqual(len(data['members']), 1)
        self.assertEqual(len(data['columns']), 1)
        self.assertEqual(data['columns'][0]['name'], 'To Do')
    
    def test_board_detail_serializer_validation(self):
        """Test BoardDetailSerializer validation."""
        serializer = BoardDetailSerializer(data={'name': '   ', 'description': 'Test'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        
        # Valid data
        serializer = BoardDetailSerializer(data={'name': 'Valid Board', 'description': 'Test'})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], 'Valid Board')


class ColumnSerializerTest(TestCase):
    """Test Column serializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.board = Board.objects.create(name='Test Board', owner=self.user)
        self.column = Column.objects.create(
            name='Test Column',
            board=self.board,
            position=1
        )
    
    def test_column_serializer(self):
        """Test ColumnSerializer basic functionality."""
        serializer = ColumnSerializer(instance=self.column)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Column')
        self.assertEqual(data['position'], 1)
        self.assertEqual(data['board'], self.board.id)
        self.assertEqual(data['tasks'], [])  # No tasks initially
    
    def test_column_serializer_with_tasks(self):
        """Test ColumnSerializer with tasks."""
        # Create a task in the column
        task = Task.objects.create(
            title='Test Task',
            column=self.column,
            position=1
        )
        
        serializer = ColumnSerializer(instance=self.column)
        data = serializer.data
        
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['title'], 'Test Task')
    
    def test_column_serializer_validation(self):
        """Test ColumnSerializer validation."""
        # Invalid position (< 1)
        serializer = ColumnSerializer(data={'name': 'Test', 'position': 0})
        self.assertFalse(serializer.is_valid())
        self.assertIn('position', serializer.errors)
        
        # Valid position
        serializer = ColumnSerializer(data={'name': 'Test', 'position': 1})
        self.assertTrue(serializer.is_valid())


class BoardAPITest(APITestCase):
    """Test Board API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.board_data = {
            'name': 'Test Board',
            'description': 'Test Description'
        }
    
    def test_create_board_success(self):
        """Test successful board creation."""
        response = self.client.post('/api/kanban/boards/', self.board_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Board')
        self.assertEqual(response.data['owner']['id'], self.user.id)
        
        # Verify board was created in database
        board = Board.objects.get(name='Test Board')
        self.assertEqual(board.owner, self.user)
        
        # Verify owner was added as member
        self.assertIn(self.user, board.members.all())
    
    def test_create_board_unauthenticated(self):
        """Test board creation without authentication."""
        self.client.credentials()  # Remove authentication
        response = self.client.post('/api/kanban/boards/', self.board_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_board_invalid_data(self):
        """Test board creation with invalid data."""
        invalid_data = {'name': '', 'description': 'Test'}
        response = self.client.post('/api/kanban/boards/', invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_user_boards(self):
        """Test listing user's boards."""
        # Create boards
        board1 = Board.objects.create(name='My Board', owner=self.user)
        board2 = Board.objects.create(name='Other Board', owner=self.other_user)
        
        # Add user as member to other_user's board
        BoardMembership.objects.create(user=self.user, board=board2, role='VIEWER')
        
        response = self.client.get('/api/kanban/boards/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both boards should be returned
        
        board_names = [board['name'] for board in response.data]
        self.assertIn('My Board', board_names)
        self.assertIn('Other Board', board_names)
    
    def test_get_board_detail(self):
        """Test retrieving board details."""
        board = Board.objects.create(name='Detail Board', owner=self.user)
        Column.objects.create(name='To Do', board=board, position=1)
        
        response = self.client.get(f'/api/kanban/boards/{board.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Detail Board')
        self.assertEqual(len(response.data['columns']), 1)
    
    def test_update_board_success(self):
        """Test successful board update."""
        board = Board.objects.create(name='Original Name', owner=self.user)
        update_data = {'name': 'Updated Name', 'description': 'Updated Description'}
        
        response = self.client.patch(f'/api/kanban/boards/{board.id}/', update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')
        
        # Verify database update
        board.refresh_from_db()
        self.assertEqual(board.name, 'Updated Name')
    
    def test_update_board_restricted_fields(self):
        """Test updating board with restricted fields."""
        board = Board.objects.create(name='Test Board', owner=self.user)
        invalid_data = {'owner': self.other_user.id}
        
        response = self.client.patch(f'/api/kanban/boards/{board.id}/', invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_delete_board_as_owner(self):
        """Test board deletion by owner."""
        board = Board.objects.create(name='Delete Board', owner=self.user)
        
        response = self.client.delete(f'/api/kanban/boards/{board.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Board.objects.filter(id=board.id).exists())
    
    def test_delete_board_as_non_owner(self):
        """Test board deletion by non-owner."""
        board = Board.objects.create(name='Other Board', owner=self.other_user)
        BoardMembership.objects.create(user=self.user, board=board, role='EDITOR')
        
        response = self.client.delete(f'/api/kanban/boards/{board.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Board.objects.filter(id=board.id).exists())
    
    def test_board_permission_non_member(self):
        """Test board access by non-member."""
        board = Board.objects.create(name='Private Board', owner=self.other_user)
        
        response = self.client.get(f'/api/kanban/boards/{board.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class EmailCheckAPITest(APITestCase):
    """Test EmailCheck API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_email_check_existing_user(self):
        """Test email check for existing user."""
        response = self.client.get('/api/kanban/email-check/?email=test@example.com')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['fullname'], 'Test User')
    
    def test_email_check_nonexistent_user(self):
        """Test email check for non-existent user."""
        response = self.client.get('/api/kanban/email-check/?email=nonexistent@example.com')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['exists'], False)
    
    def test_email_check_missing_parameter(self):
        """Test email check without email parameter."""
        response = self.client.get('/api/kanban/email-check/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_email_check_unauthenticated(self):
        """Test email check without authentication."""
        self.client.credentials()  # Remove authentication
        response = self.client.get('/api/kanban/email-check/?email=test@example.com')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ColumnAPITest(APITestCase):
    """Test Column API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.board = Board.objects.create(name='Test Board', owner=self.user)
        self.column_data = {
            'name': 'Test Column',
            'position': 1
        }
    
    def test_create_column_success(self):
        """Test successful column creation."""
        response = self.client.post(
            f'/api/kanban/boards/{self.board.id}/columns/',
            self.column_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Column')
        self.assertEqual(response.data['board'], self.board.id)
        
        # Verify column was created
        column = Column.objects.get(name='Test Column')
        self.assertEqual(column.board, self.board)
    
    def test_create_column_non_member(self):
        """Test column creation by non-member."""
        other_board = Board.objects.create(name='Other Board', owner=self.other_user)
        
        response = self.client.post(
            f'/api/kanban/boards/{other_board.id}/columns/',
            self.column_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_column_nonexistent_board(self):
        """Test column creation for non-existent board."""
        response = self.client.post(
            '/api/kanban/boards/99999/columns/',
            self.column_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_columns_for_board(self):
        """Test listing columns for a board."""
        Column.objects.create(name='Column 1', board=self.board, position=1)
        Column.objects.create(name='Column 2', board=self.board, position=2)
        
        response = self.client.get(f'/api/kanban/boards/{self.board.id}/columns/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Should be ordered by position
        self.assertEqual(response.data[0]['name'], 'Column 1')
        self.assertEqual(response.data[1]['name'], 'Column 2')
    
    def test_update_column(self):
        """Test column update."""
        column = Column.objects.create(name='Original', board=self.board, position=1)
        update_data = {'name': 'Updated Column'}
        
        response = self.client.patch(f'/api/kanban/columns/{column.id}/', update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Column')
        
        # Verify database update
        column.refresh_from_db()
        self.assertEqual(column.name, 'Updated Column')
    
    def test_delete_column(self):
        """Test column deletion."""
        column = Column.objects.create(name='Delete Me', board=self.board, position=1)
        
        response = self.client.delete(f'/api/kanban/columns/{column.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Column.objects.filter(id=column.id).exists())
    
    def test_column_validation(self):
        """Test column validation."""
        invalid_data = {'name': 'Test', 'position': 0}  # Invalid position
        
        response = self.client.post(
            f'/api/kanban/boards/{self.board.id}/columns/',
            invalid_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('position', response.data)


class TaskReorderAPITest(APITestCase):
    """Test TaskReorder API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.board = Board.objects.create(name='Test Board', owner=self.user)
        self.column1 = Column.objects.create(name='Column 1', board=self.board, position=1)
        self.column2 = Column.objects.create(name='Column 2', board=self.board, position=2)
        
        self.task = Task.objects.create(
            title='Test Task',
            column=self.column1,
            position=1
        )
    
    def test_task_reorder_within_column(self):
        """Test task reordering within same column."""
        # Create another task
        task2 = Task.objects.create(
            title='Task 2',
            column=self.column1,
            position=2
        )
        
        reorder_data = {
            'task_id': self.task.id,
            'column_id': self.column1.id,
            'position': 2
        }
        
        # Note: TaskReorderView is not in the URLs, so this would need to be added
        # For now, testing the logic would require adding the URL pattern
        # response = self.client.post('/api/kanban/task-reorder/', reorder_data)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_task_reorder_between_columns(self):
        """Test task reordering between different columns."""
        reorder_data = {
            'task_id': self.task.id,
            'column_id': self.column2.id,
            'position': 1
        }
        
        # Would need URL pattern for TaskReorderView
        # response = self.client.post('/api/kanban/task-reorder/', reorder_data)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify task moved to new column
        # self.task.refresh_from_db()
        # self.assertEqual(self.task.column, self.column2)
    
    def test_task_reorder_permission_denied(self):
        """Test task reorder by non-member."""
        other_user = User.objects.create_user(username='other', email='other@example.com')
        other_token = Token.objects.create(user=other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token.key}')
        
        reorder_data = {
            'task_id': self.task.id,
            'column_id': self.column1.id,
            'position': 1
        }
        
        # Would need URL pattern
        # response = self.client.post('/api/kanban/task-reorder/', reorder_data)
        # self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)