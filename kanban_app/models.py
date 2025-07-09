from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ARCHIVED', 'Archived'),
        ('COMPLETED', 'Completed'),
    ]

    title = models.CharField(max_length=100)  # Geändert zurück zu title für Frontend-Kompatibilität
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_boards')
    deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def name(self):
        """Alias für title für Backend-Kompatibilität."""
        return self.title


class BoardMembership(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('EDITOR', 'Editor'),
        ('VIEWER', 'Viewer'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='VIEWER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'board']
        verbose_name = "Board Membership"
        verbose_name_plural = "Board Memberships"

    def __str__(self):
        return f"{self.user.username} - {self.board.title} ({self.role})"


class Column(models.Model):
    name = models.CharField(max_length=100)  # Geändert zu name für Frontend-Kompatibilität
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='columns')
    position = models.PositiveIntegerField()
    
    class Meta:
        verbose_name = "Column"
        verbose_name_plural = "Columns"
        ordering = ['position']
        unique_together = ['board', 'position']

    def __str__(self):
        return f"{self.name} ({self.board.title})"

    @property
    def title(self):
        """Alias für name für Backend-Kompatibilität."""
        return self.name