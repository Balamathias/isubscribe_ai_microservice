from rest_framework import serializers
from .models import Chat, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            'id', 'chat', 'sender', 'content', 'image_url', 'timestamp',
            'is_tool_call', 'tool_name', 'tool_args', 'tool_result'
        ]


class ChatSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'user_id', 'created_at', 'last_message', 'metadata']

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-timestamp').first()
        if msg:
            return MessageSerializer(msg).data
        return None


class ChatDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True)

    class Meta:
        model = Chat
        fields = ['id', 'user_id', 'created_at', 'messages', 'metadata']
