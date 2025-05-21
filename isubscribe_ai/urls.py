# filepath: c:/Users/Mathias Bala/isubscribe_ms/isubscribe_ai/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import WalletViewSet, ChatViewSet, WhatsAppWebhookView

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'chats', ChatViewSet, basename='chat')

urlpatterns = [
    path('', include(router.urls)),
    path('whatsapp/webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
