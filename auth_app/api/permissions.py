from django.db import models
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from kanban_app.models import Board, BoardMembership


def create_board_permissions():
    """
    Create custom permissions for board management.
    
    Creates the following permissions:
    - view_all_boards: Can view all boards in the system
    - create_board: Can create new boards  
    - manage_board_members: Can add/remove board members
    
    This function is idempotent - it won't create duplicate permissions.
    """
    board_content_type = ContentType.objects.get_for_model(Board)

    permissions = [
        ("view_all_boards", "Can view all boards"),
        ("create_board", "Can create a board"),
        ("manage_board_members", "Can manage board members"),
    ]

    for codename, name in permissions:
        Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=board_content_type,
        )