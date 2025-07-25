import os
import logging

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.viewsets import ViewSet, ModelViewSet

from auth.supabase import SupabaseAuthentication
from isubscribe_ai.csrf_exemption import CsrfExemptSessionAuthentication
from services.wallet import get_user_wallet


from utils.response import ResponseMixin
from .models import Chat, Message
from .serializers import ChatSerializer, ChatDetailSerializer, MessageSerializer
from services.ai_agent import run_ai_agent
from rest_framework import viewsets, status
from rest_framework.decorators import action
from services.whatsapp import whatsapp_client
from services.palmpay import PalmPayService, PalmPayCreateAccountRequest
from services.otp import OTPService
from services.pin import PINService
from services.email import send_otp_email

logger = logging.Logger(__name__)

class WalletViewSet(viewsets.ViewSet, ResponseMixin):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        GET /wallet/  —  return the current user's wallet
        """
        user = request.user
        wallet, error = get_user_wallet(user.id)

        if wallet:
            return self.response(wallet, status_code=status.HTTP_200_OK)

        if error:
            return self.response(
                message=getattr(error, "message", str(error)),
                error={"detail": str(error)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return self.response(
            message="Wallet not found.",
            error={"detail": "Wallet not found."},
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ChatViewSet(viewsets.ModelViewSet, ResponseMixin):
    permission_classes = [IsAuthenticated]
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Chat.objects.filter(user_id=getattr(self.request.user, "id")).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ChatDetailSerializer
        return ChatSerializer

    def perform_create(self, serializer):
        print("Creating chat for user:", getattr(self.request.user, "id"))
        serializer.save(user_id=getattr(self.request.user, "id"))

    def create(self, request):
        """
        POST /chats/  —  create a new chat
        """
        try:
            data = request.data.copy()
            data["user_id"] = getattr(request.user, "id")
            
            metadata = data.get("metadata", {})
            # Add any user metadata that might be useful for the AI
            if hasattr(request.user, "metadata") and request.user.metadata:
                metadata.update({"user_metadata": request.user.metadata})
            data["metadata"] = metadata
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return self.response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return self.response(
                message="Failed to create chat.",
                error={"detail": str(e)},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def message(self, request, *args, **kwargs):
        """
        POST /chats/{pk}/message/  —  add a user message, run AI, return assistant response
        """
        chat = self.get_object()
        content = request.data.get("content", "")
        image_url = request.data.get("image_url")
        model = request.data.get("model", "gemini-2.0-flash")
        
        # Save the user message
        user_message = Message.objects.create(
            chat=chat, sender="user", content=content or "", image_url=image_url or None
        )
        
        try:
            # Build message history in a way that works for Gemini
            history = []
            for msg in chat.messages.order_by("timestamp"):
                # Skip the message we just created
                if msg.id == user_message.id:
                    continue
                
                if msg.is_tool_call:
                    # For tool call messages, format for Gemini
                    history.append({
                        "role": "assistant",
                        "content": msg.content
                    })
                    
                    # No need to add function calls to history for Gemini's automatic function calling
                else:
                    # For regular messages
                    history.append({
                        "role": msg.sender,
                        "content": msg.content or (f"[Image] {msg.image_url}" if msg.image_url else "")
                    })

            # Get AI response
            ai_response = run_ai_agent(user_input=content, history=history, model=model, request=request)
            
            if ai_response.get("error"):
                return self.response(
                    MessageSerializer(assistant_msg).data, 
                    error={"detail": ai_response.get('content')},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Handle tool calls
            if ai_response.get("tool_call"):
                tool_call = ai_response.get("tool_call", {})
                tool_result = ai_response.get("tool_result", {})
                
                # Create a tool call message
                assistant_msg = Message.objects.create(
                    chat=chat,
                    sender="assistant",
                    content=ai_response.get("content", ""),
                    is_tool_call=True,
                    tool_name=tool_call.get("name"),
                    tool_args=tool_call.get("arguments"),
                    tool_result=tool_result
                )
                
                # Update chat metadata with recent transaction info if available
                if "tx_id" in tool_result:
                    if not chat.metadata:
                        chat.metadata = {}
                    chat.metadata["last_transaction"] = {
                        "tx_id": tool_result.get("tx_id"),
                        "status": tool_result.get("status"),
                        "timestamp": assistant_msg.timestamp.isoformat()
                    }
                    chat.save()
                
            else:
                # Create regular text response
                assistant_msg = Message.objects.create(
                    chat=chat, 
                    sender="assistant", 
                    content=ai_response.get("content", "")
                )
                
            return self.response(
                MessageSerializer(assistant_msg).data, status=status.HTTP_200_OK
            )
        except Exception as e:
            # Create error message
            assistant_msg = Message.objects.create(
                chat=chat,
                sender="assistant",
                content=f"Sorry, an error occurred: {str(e)}"
            )
            return self.response(
                MessageSerializer(assistant_msg).data,
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WhatsAppWebhookView(APIView):
    """Handle incoming WhatsApp webhook requests"""
    permission_classes = []  # No authentication needed for webhook
    
    def get(self, request):
        """Handle webhook verification from WhatsApp"""
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN")
        
        if mode == "subscribe" and token == verify_token:
            return Response(int(challenge))
        
        return Response("Verification failed", status=status.HTTP_403_FORBIDDEN)
    
    def post(self, request):
        """Handle incoming messages from WhatsApp"""
        result = whatsapp_client.handle_webhook(request.data)
        
        if result.get("success"):
            return Response({"status": "ok"})
        else:
            return Response(
                {"status": "error", "message": result.get("error")},
                status=status.HTTP_400_BAD_REQUEST
            )


from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name="dispatch")
class CreateVirtualAccountAPIView(APIView, ResponseMixin):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        try:
            customer_name = request.data.get("customer_name")
            email = request.data.get("email")
            
            if not customer_name or not email:
                return self.response(
                    {
                        "message": "customer_name and email are required.",
                        "error": {"detail": "Missing required fields"},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            palm_pay_service = PalmPayService()
            request_data = PalmPayCreateAccountRequest(
                customer_name=customer_name,
                email=email
            )
            
            response = palm_pay_service.create_virtual_account(request_data)
            print("PalmPay response:", response)
            
            if response.status:
                return self.response(
                    {
                        "virtual_account_no": response.data.virtual_account_no,
                        "virtual_account_name": response.data.virtual_account_name,
                        "account_reference": response.data.account_reference,
                        "status": response.data.status,
                        "message": response.resp_msg,
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return self.response(
                    {
                        "message": response.resp_msg,
                        "error": {"detail": f"PalmPay error: {response.resp_msg}"},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
                
        except Exception as e:
            print(f"Error creating PalmPay virtual account: {e}")
            return self.response(
                {
                    "message": "Failed to create virtual account.",
                    "error": {"detail": str(e)},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        

def health_check(request):
    return JsonResponse({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class PINResetRequestView(APIView, ResponseMixin):
    """Request OTP for PIN reset"""
    permission_classes = []
    
    def post(self, request):
        """Send OTP email for PIN reset"""
        try:
            user = request.user
            
            if not user or not hasattr(user, 'id'):
                return self.response(
                    error={"detail": "You must be signed in to request a PIN reset"},
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            valid_otp = OTPService.get_valid_otp_for_user(user.id)
            
            if not valid_otp:
                otp_data, error = OTPService.create_otp_request(user.id)
                
                if error:
                    return self.response(
                        error={"detail": f"Error creating OTP: {str(error)}"},
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                valid_otp = otp_data
            
            if not valid_otp:
                return self.response(
                    error={"detail": "Failed to create or retrieve OTP"},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            email_result = send_otp_email(
                user.email,
                valid_otp['otp'],
                getattr(user, 'full_name', user.email)
            )
            
            if email_result.get('error'):
                return self.response(
                    error=email_result['error'],
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.response(
                {"message": "OTP sent successfully to your email"},
                status_code=status.HTTP_200_OK,
            )
            
        except Exception as e:
            logger.exception(f"Error in PIN reset request: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name="dispatch")
class PINResetVerifyOTPView(APIView, ResponseMixin):
    """Verify OTP for PIN reset"""
    permission_classes = []
    
    def post(self, request):
        """Verify OTP code"""
        try:
            user = request.user
            otp = request.data.get('otp')
            
            if not user or not hasattr(user, 'id'):
                return self.response(
                    error={"detail": "You must be signed in to verify OTP"},
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            if not otp:
                return self.response(
                    error={"detail": "OTP is required"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            is_valid = OTPService.verify_otp(user.id, otp)
            
            if not is_valid:
                return self.response(
                    error={"detail": "Invalid or expired OTP"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            return self.response(
                {"message": "OTP verified successfully", "verified": True},
                status_code=status.HTTP_200_OK,
            )
            
        except Exception as e:
            logger.exception(f"Error verifying OTP: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name="dispatch")
class PINResetView(APIView, ResponseMixin):
    """Reset user PIN after OTP verification"""
    permission_classes = []
    
    def post(self, request):
        """Reset PIN with new PIN and OTP verification"""
        try:
            user = request.user
            new_pin = request.data.get('new_pin')
            otp = request.data.get('otp')
            requires_otp: bool = request.data.get('requires_otp', True)
            
            if not user or not hasattr(user, 'id'):
                return self.response(
                    error={"detail": "You must be signed in to reset PIN"},
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            if not new_pin or (requires_otp and not otp):
                return self.response(
                    error={"detail": "new_pin is required" + (" and otp is required" if requires_otp else "")},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if not isinstance(new_pin, str) or not new_pin.isdigit() or len(new_pin) != 4:
                return self.response(
                    error={"detail": "PIN must be 4 digits"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            if requires_otp:
                if not otp:
                    return self.response(
                        error={"detail": "OTP is required when requires_otp is True"},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                is_valid_otp = OTPService.verify_otp(user.id, otp)
                
                if not is_valid_otp:
                    return self.response(
                        error={"detail": "Invalid or expired OTP"},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            
            success, error = PINService.update_pin(user.id, new_pin)
            
            if not success:
                return self.response(
                    error={"detail": f"Error resetting PIN: {str(error)}"},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return self.response(
                {"message": "PIN reset successfully"},
                status_code=status.HTTP_200_OK,
            )
            
        except Exception as e:
            logger.exception(f"Error resetting PIN: {str(e)}")
            return self.response(
                error={"detail": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
