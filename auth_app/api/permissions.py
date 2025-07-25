from django.db import models
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from kanban_app.models import Board, BoardMembership


def _get_board_permissions():
    """
    Get the list of board permissions to be created.
    
    Returns:
        list: List of tuples containing (codename, name) for permissions
    """
    return [
        ("view_all_boards", "Can view all boards"),
        ("create_board", "Can create a board"),
        ("manage_board_members", "Can manage board members"),
    ]


def _create_permission(codename, name, content_type):
    """
    Create a single permission if it doesn't exist.
    
    Args:
        codename (str): The permission codename
        name (str): The human-readable permission name
        content_type (ContentType): The content type for the permission
    
    Returns:
        tuple: (Permission, bool) - The permission object and created flag
    """
    return Permission.objects.get_or_create(
        codename=codename,
        name=name,
        content_type=content_type,
    )


def create_board_permissions():
    """
    Create custom permissions for board management.
    
    Creates the following permissions:
    - view_all_boards: Can view all boards in the system
    - create_board: Can create new boards  
    - manage_board_members: Can add/remove board members
    
    This function is idempotent - it won't create duplicate permissions.
    
    Raises:
        ContentType.DoesNotExist: If Board model content type doesn't exist
    """
    board_content_type = ContentType.objects.get_for_model(Board)
    permissions = _get_board_permissions()

    for codename, name in permissions:
        _create_permission(codename, name, board_content_type)