from django.db import models
import uuid
import json


class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Add metadata field to store additional chat info
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Chat {self.id} for {self.user_id}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.CharField(max_length=20, choices=[('user', 'user'), ('assistant', 'assistant')])
    content = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Fields for tool calls
    is_tool_call = models.BooleanField(default=False)
    tool_name = models.CharField(max_length=100, blank=True, null=True)
    tool_args = models.JSONField(default=dict, blank=True, null=True)
    tool_result = models.JSONField(default=dict, blank=True, null=True)
    
    def __str__(self):
        if self.is_tool_call:
            return f"{self.sender} @ {self.timestamp}: Tool call to {self.tool_name}"
        return f"{self.sender} @ {self.timestamp}: {self.content[:20]}"
    
    @property
    def formatted_tool_args(self):
        if self.tool_args:
            return json.dumps(self.tool_args, indent=2)
        return ""
    
    @property
    def formatted_tool_result(self):
        if self.tool_result:
            return json.dumps(self.tool_result, indent=2)
        return ""
