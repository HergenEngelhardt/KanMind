from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    """
    Task model representing individual tasks within columns.
    
    Tasks can be assigned to users and have reviewers.
    They maintain position ordering within their column.
    """
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    column = models.ForeignKey(
        "kanban_app.Column", 
        on_delete=models.CASCADE, 
        related_name="tasks"
    )
    position = models.IntegerField()
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        null=True,
        blank=True,
    )
    reviewers = models.ManyToManyField(
        User, 
        related_name="reviewing_tasks", 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position"]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return self.title


class Comment(models.Model):
    """
    Comment model for task discussions.
    
    Users can comment on tasks to provide updates or feedback.
    Comments are ordered by creation time.
    """
    
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name="comments"
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"