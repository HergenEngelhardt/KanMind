from django.contrib import admin
from .models import Task, Comment

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'column', 'assignee', 'priority', 'status', 'due_date', 'created_at']
    list_filter = ['priority', 'status', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'created_by', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'task__title']
    ordering = ['-created_at']