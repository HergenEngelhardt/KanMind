from django.db import models
from django.contrib.auth.models import User
from kanban_app.models import Column

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    column = models.ForeignKey('kanban_app.Column', on_delete=models.CASCADE, related_name='tasks')
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return self.title