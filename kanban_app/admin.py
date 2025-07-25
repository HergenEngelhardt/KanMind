from django.contrib import admin
from .models import Board, BoardMembership, Column


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Django admin configuration for Board model.
    
    Provides customized admin interface for managing Board instances
    with filtering, searching, and display options.
    """
    
    list_display = ['title', 'owner', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description']


@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
    """Django admin configuration for BoardMembership model.
    
    Provides customized admin interface for managing BoardMembership instances
    with filtering and display options for user-board relationships.
    """
    
    list_display = ['user', 'board', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    """Django admin configuration for Column model.
    
    Provides customized admin interface for managing Column instances
    with filtering, searching, and ordering options.
    """
    
    list_display = ['title', 'board', 'position', 'created_at']
    list_filter = ['board', 'position']
    search_fields = ['title']
    ordering = ['board', 'position']