import os
import requests
import json
import logging
from typing import Dict, Optional, List, Any, Union
from dotenv import load_dotenv

from services.ai_tools import run_ai_agent
from isubscribe_ai.models import Chat, Message

load_dotenv()

logger = logging.getLogger(__name__)

# WhatsApp Business API Configuration
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

class WhatsAppClient:
    def __init__(self):
        self.api_url = WHATSAPP_API_URL
        self.token = WHATSAPP_API_TOKEN
        self.phone_id = WHATSAPP_PHONE_ID
        
    def send_message(self, recipient_phone: str, message_text: str) -> Dict[str, Any]:
        """Send a text message to a WhatsApp user."""
        if not self.api_url or not self.token or not self.phone_id:
            logger.error("WhatsApp API not configured properly")
            return {"success": False, "error": "WhatsApp API not configured"}
            
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient_phone,
                "type": "text",
                "text": {
                    "body": message_text
                }
            }
            
            response = requests.post(
                f"{self.api_url}/{self.phone_id}/messages",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                return {"success": False, "error": f"API Error: {response.status_code}"}
                
        except Exception as e:
            logger.exception("Error sending WhatsApp message")
            return {"success": False, "error": str(e)}

    def handle_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Process incoming webhook data from WhatsApp."""
        try:
            # Extract the message
            entry = webhook_data.get("entry", [])
            if not entry:
                return {"success": False, "error": "No entry data"}
                
            changes = entry[0].get("changes", [])
            if not changes:
                return {"success": False, "error": "No changes data"}
                
            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                # This might be a status update, not a message
                return {"success": True, "action": "no_message"}
                
            message = messages[0]
            sender = message.get("from")
            message_type = message.get("type", "")
            
            if message_type == "text":
                text = message.get("text", {}).get("body", "")
                return self.process_incoming_message(sender, text)
            else:
                # Handle other message types like images, audio, etc.
                return {"success": False, "error": f"Unsupported message type: {message_type}"}
                
        except Exception as e:
            logger.exception("Error processing webhook")
            return {"success": False, "error": str(e)}
    
    def process_incoming_message(self, user_phone: str, message_text: str) -> Dict[str, Any]:
        """Process an incoming message and generate a response using AI."""
        try:
            # Get or create chat for this user
            chat, created = Chat.objects.get_or_create(
                user_id=user_phone,
                defaults={"metadata": {"source": "whatsapp"}}
            )
            
            # Add user message to chat
            Message.objects.create(
                chat=chat,
                sender="user",
                content=message_text
            )
            
            # Get chat history
            history = []
            for msg in chat.messages.order_by("timestamp"):
                if msg.is_tool_call:
                    # Add tool calls to history
                    history.append({
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": msg.tool_name,
                            "arguments": msg.tool_args
                        }
                    })
                    
                    # Add function response
                    history.append({
                        "role": "function", 
                        "name": msg.tool_name,
                        "content": str(msg.tool_result)
                    })
                else:
                    # Add regular messages
                    history.append({
                        "role": msg.sender,
                        "content": msg.content
                    })
            
            # Get AI response
            ai_response = run_ai_agent(history=history)
            
            # Handle tool calls or text responses
            if ai_response.get("tool_call"):
                tool_call = ai_response.get("tool_call", {})
                tool_result = ai_response.get("tool_result", {})
                
                # Create a message with the tool call
                assistant_msg = Message.objects.create(
                    chat=chat,
                    sender="assistant",
                    content=ai_response.get("content", ""),
                    is_tool_call=True,
                    tool_name=tool_call.get("name"),
                    tool_args=tool_call.get("arguments"),
                    tool_result=tool_result
                )
                
                # Update chat metadata
                if "tx_id" in tool_result:
                    chat.metadata["last_transaction"] = {
                        "tx_id": tool_result.get("tx_id"),
                        "status": tool_result.get("status")
                    }
                    chat.save()
                
                # Format response for WhatsApp
                response_text = f"{ai_response.get('content', '')}\n\n"
                if tool_result:
                    if "status" in tool_result:
                        response_text += f"Status: {tool_result.get('status')}\n"
                    if "tx_id" in tool_result:
                        response_text += f"Transaction ID: {tool_result.get('tx_id')}\n"
                    if "new_balance" in tool_result:
                        response_text += f"New Balance: {tool_result.get('new_balance')}"
            else:
                # Just a text response
                response_text = ai_response.get("content", "")
                
                # Create the message
                Message.objects.create(
                    chat=chat,
                    sender="assistant",
                    content=response_text
                )
            
            # Send the response via WhatsApp
            send_result = self.send_message(user_phone, response_text)
            
            return {
                "success": True,
                "response_sent": send_result.get("success", False),
                "chat_id": str(chat.id)
            }
            
        except Exception as e:
            logger.exception("Error processing message")
            # Try to send error message to user
            self.send_message(user_phone, "Sorry, I encountered an error processing your request.")
            return {"success": False, "error": str(e)}

# Initialize WhatsApp client
whatsapp_client = WhatsAppClient()
