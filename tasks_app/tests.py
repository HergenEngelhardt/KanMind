from django.test import TestCase
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.db import IntegrityError
from tasks_app.models import Task, Comment
from tasks_app.api.serializers import TaskSerializer, CommentSerializer, UserSerializer
from tasks_app.api.permissions import (
    IsTaskBoardMember, 
    IsTaskAssigneeOrBoardOwner, 
    IsCommentAuthorOrBoardOwner,
    IsTaskReviewer
)
from kanban_app.models import Board, Column, BoardMembership


class TaskModelTest(TestCase):
    """Test Task model functionality."""
    
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
            owner=self.user
        )
        self.column = Column.objects.create(
            name='To Do',
            board=self.board,
            position=1
        )
    
    def test_task_creation(self):
        """Test task creation with valid data."""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            column=self.column,
            position=1,
            assignee=self.user
        )
        
        self.assertEqual(str(task), 'Test Task')
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.description, 'Test Description')
        self.assertEqual(task.column, self.column)
        self.assertEqual(task.position, 1)
        self.assertEqual(task.assignee, self.user)
    
    def test_task_without_assignee(self):
        """Test task creation without assignee."""
        task = Task.objects.create(
            title='Unassigned Task',
            column=self.column,
            position=1
        )
        
        self.assertIsNone(task.assignee)
        self.assertEqual(task.title, 'Unassigned Task')
    
    def test_task_meta_options(self):
        """Test task meta options."""
        task1 = Task.objects.create(title='Task 1', column=self.column, position=2)
        task2 = Task.objects.create(title='Task 2', column=self.column, position=1)
        
        tasks = Task.objects.all()
        # Should be ordered by position
        self.assertEqual(tasks[0], task2)  # position 1
        self.assertEqual(tasks[1], task1)  # position 2
    
    def test_task_reviewers_relationship(self):
        """Test task reviewers many-to-many relationship."""
        reviewer = User.objects.create_user(username='reviewer', email='reviewer@example.com')
        task = Task.objects.create(
            title='Review Task',
            column=self.column,
            position=1
        )
        
        task.reviewers.add(reviewer)
        self.assertIn(reviewer, task.reviewers.all())
        self.assertEqual(task.reviewers.count(), 1)
    
    def test_task_column_relationship(self):
        """Test task-column foreign key relationship."""
        task = Task.objects.create(
            title='Column Task',
            column=self.column,
            position=1
        )
        
        self.assertEqual(task.column, self.column)
        self.assertIn(task, self.column.tasks.all())
    
    def test_task_assignee_set_null(self):
        """Test task assignee SET_NULL on user deletion."""
        assignee = User.objects.create_user(username='assignee', email='assignee@example.com')
        task = Task.objects.create(
            title='Assigned Task',
            column=self.column,
            position=1,
            assignee=assignee
        )
        
        # Delete assignee user
        assignee.delete()
        task.refresh_from_db()
        
        self.assertIsNone(task.assignee)


class CommentModelTest(TestCase):
    """Test Comment model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.board = Board.objects.create(name='Test Board', owner=self.user)
        self.column = Column.objects.create(name='To Do', board=self.board, position=1)
        self.task = Task.objects.create(
            title='Test Task',
            column=self.column,
            position=1
        )
    
    def test_comment_creation(self):
        """Test comment creation."""
        comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Test comment content'
        )
        
        self.assertEqual(str(comment), f'Comment by {self.user.username} on {self.task.title}')
        self.assertEqual(comment.content, 'Test comment content')
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.task, self.task)
    
    def test_comment_meta_options(self):
        """Test comment meta options."""
        comment1 = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='First comment'
        )
        comment2 = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Second comment'
        )
        
        comments = Comment.objects.all()
        # Should be ordered by created_at
        self.assertEqual(comments[0], comment1)
        self.assertEqual(comments[1], comment2)
    
    def test_comment_task_relationship(self):
        """Test comment-task foreign key relationship."""
        comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Task comment'
        )
        
        self.assertEqual(comment.task, self.task)
        self.assertIn(comment, self.task.comments.all())


class UserSerializerTest(TestCase):
    """Test UserSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_serializer(self):
        """Test UserSerializer basic functionality."""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')


class CommentSerializerTest(TestCase):
    """Test CommentSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.board = Board.objects.create(name='Test Board', owner=self.user)
        self.column = Column.objects.create(name='To Do', board=self.board, position=1)
        self.task = Task.objects.create(title='Test Task', column=self.column, position=1)
        self.comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Test comment'
        )
    
    def test_comment_serializer(self):
        """Test CommentSerializer basic functionality."""
        serializer = CommentSerializer(instance=self.comment)
        data = serializer.data
        
        self.assertEqual(data['content'], 'Test comment')
        self.assertEqual(data['author']['id'], self.user.id)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
    
    def test_comment_content_validation(self):
        """Test comment content validation."""
        # Empty content
        serializer = CommentSerializer(data={'content': ''})
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)
        
        # Whitespace only
        serializer = CommentSerializer(data={'content': '   '})
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)
        
        # Valid content
        serializer = CommentSerializer(data={'content': 'Valid comment'})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['content'], 'Valid comment')
    
    def test_comment_validation_strips_whitespace(self):
        """Test comment validation strips whitespace."""
        serializer = CommentSerializer(data={'content': '  Valid comment  '})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['content'], 'Valid comment')


class TaskSerializerTest(TestCase):
    """Test TaskSerializer functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.board = Board.objects.create(name='Test Board', owner=self.user)
        self.column = Column.objects.create(name='To Do', board=self.board, position=1)
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            column=self.column,
            position=1,
            assignee=self.user
        )
    
    def test_task_serializer(self):
        """Test TaskSerializer basic functionality."""
        serializer = TaskSerializer(instance=self.task)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Test Task')
        self.assertEqual(data['description'], 'Test Description')
        self.assertEqual(data['column'], self.column.id)
        self.assertEqual(data['position'], 1)
        self.assertEqual(data['assignee']['id'], self.user.id)
        self.assertEqual(data['comments'], [])
        self.assertEqual(data['reviewers'], [])
    
    def test_task_serializer_with_comments(self):
        """Test TaskSerializer with comments."""
        Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Test comment'
        )
        
        serializer = TaskSerializer(instance=self.task)
        data = serializer.data
        
        self.assertEqual(len(data['comments']), 1)
        self.assertEqual(data['comments'][0]['content'], 'Test comment')
    
    def test_task_serializer_with_reviewers(self):
        """Test TaskSerializer with reviewers."""
        reviewer = User.objects.create_user(username='reviewer', email='reviewer@example.com')
        self.task.reviewers.add(reviewer)
        
        serializer = TaskSerializer(instance=self.task)
        data = serializer.data
        
        self.assertEqual(len(data['reviewers']), 1)
        self.assertEqual(data['reviewers'][0]['username'], 'reviewer')
    
    def test_task_title_validation(self):
        """Test task title validation."""
        # Empty title
        serializer = TaskSerializer(data={'title': '', 'position': 1})
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        
        # Whitespace only
        serializer = TaskSerializer(data={'title': '   ', 'position': 1})
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        
        # Valid title
        serializer = TaskSerializer(data={'title': 'Valid Task', 'position': 1})
        self.assertTrue(serializer.is_valid())
    
    def test_task_position_validation(self):
        """Test task position validation."""
        # Negative position
        serializer = TaskSerializer(data={'title': 'Test', 'position': -1})
        self.assertFalse(serializer.is_valid())
        self.assertIn('position', serializer.errors)
        
        # Zero position (valid)
        serializer = TaskSerializer(data={'title': 'Test', 'position': 0})
        self.assertTrue(serializer.is_valid())
        
        # Positive position
        serializer = TaskSerializer(data={'title': 'Test', 'position': 5})
        self.assertTrue(serializer.is_valid())
    
    def test_task_update_basic_fields(self):
        """Test task update with basic fields."""
        from unittest.mock import Mock
        
        request = Mock()
        request.data = {'title': 'Updated Title', 'description': 'Updated Description'}
        
        serializer = TaskSerializer(
            instance=self.task,
            data={'title': 'Updated Title', 'description': 'Updated Description'},
            context={'request': request},
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_task = serializer.save()
        
        self.assertEqual(updated_task.title, 'Updated Title')
        self.assertEqual(updated_task.description, 'Updated Description')
    
    def test_task_update_assignee(self):
        """Test task update with assignee."""
        from unittest.mock import Mock
        
        new_assignee = User.objects.create_user(username='newassignee', email='new@example.com')
        
        request = Mock()
        request.data = {'assignee': new_assignee.id}
        
        serializer = TaskSerializer(
            instance=self.task,
            data={},
            context={'request': request},
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_task = serializer.save()
        
        self.assertEqual(updated_task.assignee, new_assignee)
    
    def test_task_update_reviewers(self):
        """Test task update with reviewers."""
        from unittest.mock import Mock
        
        reviewer1 = User.objects.create_user(username='reviewer1', email='r1@example.com')
        reviewer2 = User.objects.create_user(username='reviewer2', email='r2@example.com')
        
        request = Mock()
        request.data = {'reviewers': [reviewer1.id, reviewer2.id]}
        
        serializer = TaskSerializer(
            instance=self.task,
            data={},
            context={'request': request},
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_task = serializer.save()
        
        self.assertIn(reviewer1, updated_task.reviewers.all())
        self.assertIn(reviewer2, updated_task.reviewers.all())
        self.assertEqual(updated_task.reviewers.count(), 2)


class TaskPermissionsTest(TestCase):
    """Test Task permission classes."""
    
    def setUp(self):
        """Set up test data."""
        self.owner = User.objects.create_user(username='owner', email='owner@example.com')
        self.member = User.objects.create_user(username='member', email='member@example.com')
        self.stranger = User.objects.create_user(username='stranger', email='stranger@example.com')
        
        self.board = Board.objects.create(name='Test Board', owner=self.owner)
        BoardMembership.objects.create(user=self.member, board=self.board, role='EDITOR')
        
        self.column = Column.objects.create(name='To Do', board=self.board, position=1)
        self.task = Task.objects.create(
            title='Test Task',
            column=self.column,
            position=1,
            assignee=self.member
        )
    
    def test_is_task_board_member_permission(self):
        """Test IsTaskBoardMember permission."""
        permission = IsTaskBoardMember()
        
        from unittest.mock import Mock
        request = Mock()
        view = Mock()
        
        # Owner should have permission
        request.user = self.owner
        self.assertTrue(permission.has_object_permission(request, view, self.task))
        
        # Member should have permission
        request.user = self.member
        self.assertTrue(permission.has_object_permission(request, view, self.task))
        
        # Stranger should not have permission
        request.user = self.stranger
        self.assertFalse(permission.has_object_permission(request, view, self.task))
    
    def test_is_task_assignee_or_board_owner_permission(self):
        """Test IsTaskAssigneeOrBoardOwner permission."""
        permission = IsTaskAssigneeOrBoardOwner()
        
        from unittest.mock import Mock
        request = Mock()
        view = Mock()
        
        # Owner should have permission
        request.user = self.owner
        self.assertTrue(permission.has_object_permission(request, view, self.task))
        
        # Assignee should have permission
        request.user = self.member  # member is assignee
        self.assertTrue(permission.has_object_permission(request, view, self.task))
        
        # Stranger should not have permission
        request.user = self.stranger
        self.assertFalse(permission.has_object_permission(request, view, self.task))
    
    def test_is_task_reviewer_permission(self):
        """Test IsTaskReviewer permission."""
        permission = IsTaskReviewer()
        
        # Add reviewer to task
        self.task.reviewers.add(self.member)
        
        from unittest.mock import Mock
        request = Mock()
        view = Mock()
        
        # Reviewer should have permission
        request.user = self.member
        self.assertTrue(permission.has_object_permission(request, view, self.task))
        
        # Non-reviewer should not have permission
        request.user = self.stranger
        self.assertFalse(permission.has_object_permission(request, view, self.task))


class TaskAPITest(APITestCase):
    """Test Task API endpoints."""
    
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
        self.column = Column.objects.create(name='To Do', board=self.board, position=1)
        
        self.task_data = {
            'title': 'Test Task',
            'description': 'Test Description',
            'column': self.column.id,
            'position': 1
        }
    
    def test_create_task_success(self):
        """Test successful task creation."""
        response = self.client.post('/api/tasks/', self.task_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Task')
        self.assertEqual(response.data['column'], self.column.id)
        
        # Verify task was created in database
        task = Task.objects.get(title='Test Task')
        self.assertEqual(task.column, self.column)
    
    def test_create_task_unauthorized(self):
        """Test task creation without authentication."""
        self.client.credentials()  # Remove authentication
        response = self.client.post('/api/tasks/', self.task_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_task_invalid_column(self):
        """Test task creation with invalid column."""
        invalid_data = self.task_data.copy()
        invalid_data['column'] = 99999
        
        response = self.client.post('/api/tasks/', invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_task_no_permission(self):
        """Test task creation without column permission."""
        other_board = Board.objects.create(name='Other Board', owner=self.other_user)
        other_column = Column.objects.create(name='Other Column', board=other_board, position=1)
        
        invalid_data = self.task_data.copy()
        invalid_data['column'] = other_column.id
        
        response = self.client.post('/api/tasks/', invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_tasks_by_column(self):
        """Test listing tasks filtered by column."""
        Task.objects.create(title='Task 1', column=self.column, position=1)
        Task.objects.create(title='Task 2', column=self.column, position=2)
        
        response = self.client.get(f'/api/tasks/?column={self.column.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_list_user_board_tasks(self):
        """Test listing all tasks from user's boards."""
        Task.objects.create(title='My Task', column=self.column, position=1)
        
        # Create task in other user's board (shouldn't appear)
        other_board = Board.objects.create(name='Other Board', owner=self.other_user)
        other_column = Column.objects.create(name='Other Column', board=other_board, position=1)
        Task.objects.create(title='Other Task', column=other_column, position=1)
        
        response = self.client.get('/api/tasks/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'My Task')
    
    def test_get_task_detail(self):
        """Test retrieving task details."""
        task = Task.objects.create(title='Detail Task', column=self.column, position=1)
        
        response = self.client.get(f'/api/tasks/{task.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Detail Task')
    
    def test_update_task_as_assignee(self):
        """Test task update by assignee."""
        task = Task.objects.create(
            title='Original Task',
            column=self.column,
            position=1,
            assignee=self.user
        )
        
        update_data = {'title': 'Updated Task'}
        response = self.client.patch(f'/api/tasks/{task.id}/', update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Task')
    
    def test_update_task_as_board_owner(self):
        """Test task update by board owner."""
        task = Task.objects.create(
            title='Owner Task',
            column=self.column,
            position=1,
            assignee=self.other_user
        )
        
        update_data = {'title': 'Updated by Owner'}
        response = self.client.patch(f'/api/tasks/{task.id}/', update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated by Owner')
    
    def test_delete_task(self):
        """Test task deletion."""
        task = Task.objects.create(title='Delete Task', column=self.column, position=1)
        
        response = self.client.delete(f'/api/tasks/{task.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task.id).exists())
    
    def test_get_assigned_tasks(self):
        """Test getting tasks assigned to current user."""
        Task.objects.create(
            title='Assigned Task',
            column=self.column,
            position=1,
            assignee=self.user
        )
        Task.objects.create(
            title='Unassigned Task',
            column=self.column,
            position=2
        )
        
        response = self.client.get('/api/tasks/assignee-me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Assigned Task')
    
    def test_get_reviewing_tasks(self):
        """Test getting tasks being reviewed by current user."""
        task = Task.objects.create(title='Review Task', column=self.column, position=1)
        task.reviewers.add(self.user)
        
        response = self.client.get('/api/tasks/reviewing/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Review Task')


class CommentAPITest(APITestCase):
    """Test Comment API endpoints."""
    
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
        self.column = Column.objects.create(name='To Do', board=self.board, position=1)
        self.task = Task.objects.create(title='Test Task', column=self.column, position=1)
        
        self.comment_data = {
            'content': 'Test comment content'
        }
    
    def test_create_comment_success(self):
        """Test successful comment creation."""
        response = self.client.post(
            f'/api/tasks/{self.task.id}/comments/',
            self.comment_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Test comment content')
        self.assertEqual(response.data['author']['id'], self.user.id)
        
        # Verify comment was created
        comment = Comment.objects.get(content='Test comment content')
        self.assertEqual(comment.task, self.task)
        self.assertEqual(comment.author, self.user)
    
    def test_create_comment_no_permission(self):
        """Test comment creation without board access."""
        other_board = Board.objects.create(name='Other Board', owner=self.other_user)
        other_column = Column.objects.create(name='Other Column', board=other_board, position=1)
        other_task = Task.objects.create(title='Other Task', column=other_column, position=1)
        
        response = self.client.post(
            f'/api/tasks/{other_task.id}/comments/',
            self.comment_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_task_comments(self):
        """Test listing comments for a task."""
        Comment.objects.create(
            task=self.task,
            author=self.user,
            content='First comment'
        )
        Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Second comment'
        )
        
        response = self.client.get(f'/api/tasks/{self.task.id}/comments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_delete_comment_as_author(self):
        """Test comment deletion by author."""
        comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Delete me'
        )
        
        response = self.client.delete(f'/api/tasks/{self.task.id}/comments/{comment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())
    
    def test_delete_comment_as_board_owner(self):
        """Test comment deletion by board owner."""
        comment = Comment.objects.create(
            task=self.task,
            author=self.other_user,
            content='Board owner can delete'
        )
        
        response = self.client.delete(f'/api/tasks/{self.task.id}/comments/{comment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())
    
    def test_delete_comment_no_permission(self):
        """Test comment deletion without permission."""
        # Create comment by other user
        comment = Comment.objects.create(
            task=self.task,
            author=self.other_user,
            content='Cannot delete'
        )
        
        # Switch to different user (not board owner)
        other_token = Token.objects.create(user=self.other_user)
        other_board = Board.objects.create(name='Other Board', owner=self.other_user)
        other_column = Column.objects.create(name='Other Column', board=other_board, position=1)
        other_task = Task.objects.create(title='Other Task', column=other_column, position=1)
        
        # Create comment by original user in other board
        other_comment = Comment.objects.create(
            task=other_task,
            author=self.user,
            content='Other comment'
        )
        
        # Try to delete as non-author, non-board-owner
        response = self.client.delete(f'/api/tasks/{other_task.id}/comments/{other_comment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_comment_invalid_data(self):
        """Test comment creation with invalid data."""
        invalid_data = {'content': ''}
        response = self.client.post(
            f'/api/tasks/{self.task.id}/comments/',
            invalid_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_comment_nonexistent_task(self):
        """Test comment creation for non-existent task."""
        response = self.client.post(
            '/api/tasks/99999/comments/',
            self.comment_data
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TaskAPIIntegrationTest(APITestCase):
    """Integration tests for Task API with complex scenarios."""
    
    def setUp(self):
        """Set up complex test scenario."""
        # Create users
        self.owner = User.objects.create_user(username='owner', email='owner@example.com')
        self.member = User.objects.create_user(username='member', email='member@example.com')
        self.assignee = User.objects.create_user(username='assignee', email='assignee@example.com')
        
        # Create board with members
        self.board = Board.objects.create(name='Project Board', owner=self.owner)
        BoardMembership.objects.create(user=self.member, board=self.board, role='EDITOR')
        BoardMembership.objects.create(user=self.assignee, board=self.board, role='VIEWER')
        
        # Create columns
        self.todo_column = Column.objects.create(name='To Do', board=self.board, position=1)
        self.progress_column = Column.objects.create(name='In Progress', board=self.board, position=2)
        self.done_column = Column.objects.create(name='Done', board=self.board, position=3)
        
        # Authenticate as owner
        self.token = Token.objects.create(user=self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_task_workflow_integration(self):
        """Test complete task workflow."""
        # 1. Create task
        task_data = {
            'title': 'Implement Feature X',
            'description': 'Add new feature to the application',
            'column': self.todo_column.id,
            'position': 1
        }
        response = self.client.post('/api/tasks/', task_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_id = response.data['id']
        
        # 2. Assign task and add reviewers
        update_data = {
            'assignee': self.assignee.id,
            'reviewers': [self.member.id]
        }
        response = self.client.patch(f'/api/tasks/{task_id}/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Add comment as assignee
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {Token.objects.get_or_create(user=self.assignee)[0].key}')
        comment_data = {'content': 'Started working on this task'}
        response = self.client.post(f'/api/tasks/{task_id}/comments/', comment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 4. Move task to In Progress
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')  # Back to owner
        move_data = {
            'column': self.progress_column.id,
            'position': 1
        }
        response = self.client.patch(f'/api/tasks/{task_id}/', move_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 5. Complete task
        complete_data = {
            'column': self.done_column.id,
            'position': 1
        }
        response = self.client.patch(f'/api/tasks/{task_id}/', complete_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 6. Verify final state
        response = self.client.get(f'/api/tasks/{task_id}/')
        task_data = response.data
        
        self.assertEqual(task_data['column'], self.done_column.id)
        self.assertEqual(task_data['assignee']['id'], self.assignee.id)
        self.assertEqual(len(task_data['reviewers']), 1)
        self.assertEqual(len(task_data['comments']), 1)
    
    def test_board_member_permissions(self):
        """Test different permission levels for board members."""
        # Create task as owner
        task = Task.objects.create(
            title='Permission Test Task',
            column=self.todo_column,
            position=1,
            assignee=self.assignee
        )
        
        # Test as member (can view, cannot update if not assignee)
        member_token = Token.objects.get_or_create(user=self.member)[0]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {member_token.key}')
        
        # Can view
        response = self.client.get(f'/api/tasks/{task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Cannot update (not assignee or owner)
        response = self.client.patch(f'/api/tasks/{task.id}/', {'title': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test as assignee (can update)
        assignee_token = Token.objects.get_or_create(user=self.assignee)[0]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {assignee_token.key}')
        
        response = self.client.patch(f'/api/tasks/{task.id}/', {'title': 'Updated by Assignee'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated by Assignee')