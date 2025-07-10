from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
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
        return self.title

    @property
    def owner_id(self):
        return self.owner.id

    @property
    def member_count(self):
        return self.members.count()

    @property
    def ticket_count(self):
        total = 0
        for column in self.columns.all():
            total += column.tasks.count()
        return total

    @property
    def tasks_to_do_count(self):
        total = 0
        for column in self.columns.all():
            total += column.tasks.filter(status='OPEN').count()
        return total

    @property
    def tasks_high_prio_count(self):
        total = 0
        for column in self.columns.all():
            total += column.tasks.filter(priority='HIGH').count()
        return total

    @property
    def tasks(self):
        from tasks_app.models import Task
        return Task.objects.filter(column__board=self)


class Column(models.Model):
    title = models.CharField(max_length=100)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='columns')
    position = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']
        unique_together = ['board', 'position']

    def __str__(self):
        return f"{self.board.title} - {self.title}"

    @property
    def name(self):
        return self.title


class BoardMembership(models.Model):
    ROLE_CHOICES = [
        ('OWNER', 'Owner'),
        ('ADMIN', 'Admin'),
        ('EDITOR', 'Editor'),
        ('VIEWER', 'Viewer'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='board_memberships')
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='board_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='EDITOR')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'board']

    def __str__(self):
        return f"{self.user.username} - {self.board.title} ({self.role})"