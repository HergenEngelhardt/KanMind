from django.contrib import admin
from .models import Task, Comment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model."""
    
    list_display = ('title', 'column', 'assignee', 'position', 'created_at')
    list_filter = ('column__board', 'assignee', 'created_at')
    search_fields = ('title', 'description', 'assignee__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('column', 'position')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for Comment model."""
    
    list_display = ('task', 'author', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'task__title', 'author__username')
    readonly_fields = ('created_at', 'updated_at')