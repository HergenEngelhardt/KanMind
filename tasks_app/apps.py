from django.apps import AppConfig


class TasksAppConfig(AppConfig):
    """
    Configuration for the Tasks app.
    
    Manages tasks and comments within Kanban boards.
    Provides task assignment, review, and discussion functionality.
    """
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "tasks_app"