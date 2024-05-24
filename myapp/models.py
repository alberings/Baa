# models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class Endpoint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField(unique=True)
    api_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    custom_js = models.TextField(blank=True, null=True, help_text="Add your custom tracking JavaScript here. Only safe JavaScript is allowed.")
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return self.url

class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    path = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField()
    session_id = models.CharField(max_length=50)  # Add default value
    
    def __str__(self):
        return f"{self.type} on {self.path} at {self.timestamp}"
