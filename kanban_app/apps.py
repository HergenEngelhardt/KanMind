from django.apps import AppConfig


class KanbanAppConfig(AppConfig):
    """
    Configuration for the Kanban app.
    
    Manages boards, columns, and board memberships.
    Provides the core Kanban functionality for project management.
    """
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "kanban_app"