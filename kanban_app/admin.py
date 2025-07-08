from django.contrib import admin
from .models import Board, Column, BoardMembership


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Admin interface for Board model."""
    
    list_display = ('title', 'owner', 'status', 'deadline', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at', 'deadline')
    search_fields = ('title', 'description', 'owner__username', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'deadline'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'owner')
        }),
        ('Project Management', {
            'fields': ('status', 'deadline')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    """Admin interface for Column model."""
    
    list_display = ('title', 'board', 'position')
    list_filter = ('board', 'board__status')
    search_fields = ('title', 'board__title')
    ordering = ('board', 'position')


@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
    """Admin interface for BoardMembership model."""
    
    list_display = ('user', 'board', 'role', 'board_status', 'board_deadline')
    list_filter = ('role', 'board__status')
    search_fields = ('user__username', 'user__email', 'board__title')
    
    def board_status(self, obj):
        """Display board status in membership admin."""
        return obj.board.status
    board_status.short_description = 'Board Status'
    
    def board_deadline(self, obj):
        """Display board deadline in membership admin."""
        return obj.board.deadline
    board_deadline.short_description = 'Board Deadline'