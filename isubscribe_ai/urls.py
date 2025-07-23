from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WalletViewSet, 
    ChatViewSet, 
    WhatsAppWebhookView, 
    CreateVirtualAccountAPIView, 
    health_check,
    PINResetRequestView,
    PINResetVerifyOTPView,
    PINResetView
)

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'chats', ChatViewSet, basename='chat')

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path('whatsapp/webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('palmpay/create_virtual_account/', CreateVirtualAccountAPIView.as_view(), name='create_virtual_account'),

    ### PIN Reset URLs
    path('pin-reset/request/', PINResetRequestView.as_view(), name='pin-reset-request'),
    path('pin-reset/verify-otp/', PINResetVerifyOTPView.as_view(), name='pin-reset-verify-otp'),
    path('pin-reset/reset/', PINResetView.as_view(), name='pin-reset'),    

    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
