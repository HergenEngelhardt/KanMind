from django.db import models
from django.contrib.auth.models import User
from kanban_app.models import Column


class Task(models.Model):
    """
    Model representing a task in the kanban board.
    
    A task can be assigned to a user, have reviewers, and belongs to a specific column.
    Tasks have priority levels, status tracking, and optional due dates.
    """
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('to-do', 'To-do'),
        ('in-progress', 'In-progress'),
        ('review', 'Review'),
        ('done', 'Done'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to-do')
    due_date = models.DateField(null=True, blank=True)
    
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name='tasks')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    reviewers = models.ManyToManyField(User, blank=True, related_name='reviewing_tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Return string representation of the task.
        
        Returns:
            str: The title of the task.
        """
        return self.title

    def is_overdue(self):
        """
        Check if the task is overdue based on due_date.
        
        Returns:
            bool: True if task is overdue, False otherwise.
        """
        from django.utils import timezone
        if not self.due_date:
            return False
        return timezone.now().date() > self.due_date

    def can_be_reviewed(self):
        """
        Check if the task is ready for review.
        
        Returns:
            bool: True if task status is 'review', False otherwise.
        """
        return self.status == 'review'

    def assign_to_user(self, user):
        """
        Assign the task to a specific user.
        
        Args:
            user (User): The user to assign the task to.
        """
        self.assignee = user
        self.save()

    class Meta:
        ordering = ['-created_at']


class Comment(models.Model):
    """
    Model representing a comment on a task.
    
    Comments are created by users and associated with specific tasks.
    They track creation and update timestamps.
    """
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Return string representation of the comment.
        
        Returns:
            str: A formatted string showing task title and comment author.
        """
        return f"Comment on {self.task.title} by {self.created_by.username}"

    def is_recent(self):
        """
        Check if the comment was created recently (within last 24 hours).
        
        Returns:
            bool: True if comment is recent, False otherwise.
        """
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() - self.created_at < timedelta(days=1)

    def get_author_name(self):
        """
        Get the full name or username of the comment author.
        
        Returns:
            str: Full name if available, otherwise username.
        """
        if self.created_by.first_name and self.created_by.last_name:
            return f"{self.created_by.first_name} {self.created_by.last_name}"
        return self.created_by.username

    class Meta:
        ordering = ['-created_at']