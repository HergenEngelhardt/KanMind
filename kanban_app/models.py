from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    """
    Kanban board model.
    
    Represents a project board containing columns and tasks.
    Each board has an owner and can have multiple members with different roles.
    """
    
    name = models.CharField(max_length=100)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class BoardMembership(models.Model):
    """
    Through model for Board-User relationship.
    
    Defines user roles within a board (Admin, Editor, Viewer).
    Ensures unique membership per user per board.
    """
    
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("EDITOR", "Editor"),
        ("VIEWER", "Viewer"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default="VIEWER"
    )

    class Meta:
        unique_together = ("user", "board")
        verbose_name = "Board Membership"
        verbose_name_plural = "Board Memberships"

    def __str__(self):
        return f"{self.user.username} - {self.board.name} ({self.role})"


class Column(models.Model):
    """
    Column model for Kanban boards.
    
    Represents a workflow stage (e.g., To Do, In Progress, Done).
    Columns are ordered by position within a board.
    """
    
    name = models.CharField(max_length=100)
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
        return f"{self.name} ({self.board.name})"