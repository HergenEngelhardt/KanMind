from django.contrib import admin
from .models import Board, BoardMembership, Column

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description']

@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'board', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']

@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ['title', 'board', 'position', 'created_at']  # ✅ Geändert von 'name' zu 'title'
    list_filter = ['board', 'position']
    search_fields = ['title']  # ✅ Geändert von 'name' zu 'title'
    ordering = ['board', 'position']