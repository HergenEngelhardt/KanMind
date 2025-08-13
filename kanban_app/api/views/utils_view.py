"""
Task formatting utilities for board views.

This module contains utility functions for formatting task data
to be included in board responses.
"""

def format_task_data(task):
    """
    Formats task data for response.
    
    Args:
        task (Task): Task instance
        
    Returns:
        dict: Task data dictionary
    """
    task_data = create_base_task_data(task)
    
    add_assignee_to_task_data(task, task_data)
    add_reviewer_to_task_data(task, task_data)
    
    return task_data
    
def create_base_task_data(task):
    """
    Creates basic task data dictionary.
    
    Args:
        task (Task): Task instance
        
    Returns:
        dict: Basic task data
    """
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'assignee': None,
        'reviewer': None,
        'due_date': task.due_date,
        'comments_count': task.comments.count()
    }
    
def add_assignee_to_task_data(task, task_data):
    """
    Adds assignee information to task data.
    
    Args:
        task (Task): Task instance
        task_data (dict): Task data dictionary to modify
    """
    if task.assignee:
        task_data['assignee'] = format_user_data(task.assignee)
        
def add_reviewer_to_task_data(task, task_data):
    """
    Adds reviewer information to task data.
    
    Args:
        task (Task): Task instance
        task_data (dict): Task data dictionary to modify
    """
    if task.reviewer.exists():
        reviewer = task.reviewer.first()
        task_data['reviewer'] = format_user_data(reviewer)

def format_user_data(user):
    """
    Formats user data for response.
    
    Args:
        user (User): User instance
        
    Returns:
        dict: User data dictionary
    """
    return {
        'id': user.id,
        'email': user.email,
        'fullname': f"{user.first_name} {user.last_name}".strip()
    }