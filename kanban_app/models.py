from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    """
    Kanban board model.
    
    Represents a project board containing columns and tasks.
    Each board has an owner and can have multiple members with different roles.
    """
    
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="owned_boards"
    )
    members = models.ManyToManyField(
        User, 
        through="BoardMembership", 
        related_name="member_boards"
    )
    deadline = models.DateTimeField(null=True, blank=True, help_text="Board deadline")
    status = models.CharField(
        max_length=20,
        choices=[
            ('PLANNING', 'Planning'),
            ('ACTIVE', 'Active'),
            ('ON_HOLD', 'On Hold'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled'),
        ],
        default='PLANNING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class BoardMembership(models.Model):
    """
    Represents the relationship between a user and a board.
    
    Defines user roles within a board (Admin, Editor, Viewer).
    Each user can have only one role per board.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=10,
        choices=[
            ("ADMIN", "Admin"),
            ("EDITOR", "Editor"),
            ("VIEWER", "Viewer"),
        ],
        default="VIEWER",
    )

    class Meta:
        unique_together = ("user", "board")
        verbose_name = "Board Membership"
        verbose_name_plural = "Board Memberships"

    def __str__(self):
        return f"{self.user.username} - {self.board.title} ({self.role})"


class Column(models.Model):
    """
    Kanban column model.
    
    Represents a column within a board (e.g., To Do, In Progress, Done).
    Columns are ordered by position within each board.
    """
    
    title = models.CharField(max_length=100)
    board = models.ForeignKey(
        Board, 
        on_delete=models.CASCADE, 
        related_name="columns"
    )
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]
        verbose_name = "Column"
        verbose_name_plural = "Columns"

    def __str__(self):
        return f"{self.board.title} - {self.title}"