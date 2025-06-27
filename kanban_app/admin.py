from django.contrib import admin
from .models import Board, Column, BoardMembership


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Admin interface for Board model."""
    
    list_display = ('name', 'owner', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    """Admin interface for Column model."""
    
    list_display = ('name', 'board', 'position')
    list_filter = ('board',)
    search_fields = ('name', 'board__name')
    ordering = ('board', 'position')


@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
    """Admin interface for BoardMembership model."""
    
    list_display = ('user', 'board', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'board__name')