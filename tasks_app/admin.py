from django.contrib import admin
from .models import Task, Comment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Django admin configuration for Task model.
    
    Provides administrative interface for managing tasks with filtering,
    searching and custom display options.
    """
    
    list_display = ['title', 'status', 'priority', 'assignee', 'column', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Django admin configuration for Comment model.
    
    Provides administrative interface for managing comments with filtering
    and custom display options.
    """
    
    list_display = ['task', 'created_by', 'created_at']
    list_filter = ['created_at']