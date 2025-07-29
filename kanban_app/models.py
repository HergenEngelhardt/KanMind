from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    """
    A Kanban board model that represents a project workspace.
    
    The Board model manages project information, members, and related tasks
    through columns. It supports different statuses and role-based access.
    """
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ARCHIVED', 'Archived'),
        ('COMPLETED', 'Completed'),
    ]

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_boards')
    members = models.ManyToManyField(User, through='BoardMembership', related_name='member_boards')
    deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"
        ordering = ['-created_at']

    def __str__(self):
        """
        Return string representation of the board.
        
        Returns:
            str: The title of the board, or fallback if title is None/empty.
        """
        return self.title or f"Board {self.id}"

    @property
    def name(self):
        """
        Alias for title to maintain API compatibility.
        
        Returns:
            str: The title of the board.
        """
        return self.title

    @name.setter
    def name(self, value):
        """
        Setter for name property to update title.
        
        Args:
            value (str): New name/title for the board
        """
        self.title = value

    @property
    def owner_id(self):
        """
        Get the ID of the board owner.
        
        Returns:
            int: The user ID of the board owner.
        """
        return self.owner.id

    @property
    def member_count(self):
        """
        Get the total number of board members.
        
        Returns:
            int: The count of members in this board.
        """
        return self.members.count()

    @property
    def ticket_count(self):
        """
        Get the total number of tasks across all columns.
        
        Returns:
            int: The total count of tasks in this board.
        """
        return self._count_tasks_by_filter()

    @property
    def tasks_to_do_count(self):
        """
        Get the count of tasks with 'to-do' status.
        
        Returns:
            int: The count of tasks with status 'to-do'.
        """
        return self._count_tasks_by_filter(status='to-do')

    @property
    def tasks_high_prio_count(self):
        """
        Get the count of high priority tasks.
        
        Returns:
            int: The count of tasks with priority 'high'.
        """
        return self._count_tasks_by_filter(priority='high')

    def _count_tasks_by_filter(self, **filters):
        """
        Count tasks across all columns with optional filters.
        
        Args:
            **filters: Optional keyword arguments to filter tasks.
        
        Returns:
            int: The count of tasks matching the filters.
        """
        total = 0
        for column in self.columns.all():
            if filters:
                total += column.tasks.filter(**filters).count()
            else:
                total += column.tasks.count()
        return total


class BoardMembership(models.Model):
    """
    Intermediate model for Board-User many-to-many relationship with roles.
    
    This model defines the relationship between users and boards, including
    their role and permissions within the board.
    """
    
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('EDITOR', 'Editor'),
        ('VIEWER', 'Viewer'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='VIEWER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'board']
        verbose_name = "Board Membership"
        verbose_name_plural = "Board Memberships"

    def __str__(self):
        """
        Return string representation of the board membership.
        
        Returns:
            str: Formatted string showing user, board title, and role.
        """
        username = self.user.username if self.user else "Unknown User"
        board_title = self.board.title if self.board and self.board.title else f"Board {self.board.id if self.board else 'Unknown'}"
        return f"{username} - {board_title} ({self.role})"


class Column(models.Model):
    """
    A column within a Kanban board that contains tasks.
    
    Columns represent different stages of work (e.g., To Do, In Progress, Done)
    and are ordered by position within their parent board.
    """
    
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='columns')
    title = models.CharField(max_length=50)
    position = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']
        unique_together = ['board', 'position']

    def __str__(self):
        """
        Return string representation of the column.
        
        Returns:
            str: Formatted string showing board title and column title.
        """
        board_title = self.board.title if self.board and self.board.title else f"Board {self.board.id if self.board else 'Unknown'}"
        column_title = self.title or f"Column {self.id}"
        return f"{board_title} - {column_title}"

    @property
    def name(self):
        """
        Alias for title to maintain API compatibility.
        
        Returns:
            str: The title of the column.
        """
        return self.title

    @property
    def status(self):
        """
        Map column title to status for API compatibility.
        
        Returns:
            str: Status based on column title.
        """
        title_lower = self.title.lower() if self.title else ""
        if 'todo' in title_lower or 'to do' in title_lower or 'to-do' in title_lower:
            return 'TODO'
        elif 'progress' in title_lower or 'doing' in title_lower:
            return 'IN_PROGRESS'
        elif 'review' in title_lower:
            return 'REVIEW'
        elif 'done' in title_lower or 'complete' in title_lower:
            return 'DONE'
        else:
            return 'TODO'  