from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import WalletViewSet, ChatViewSet, WhatsAppWebhookView, CreateVirtualAccountAPIView 

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'chats', ChatViewSet, basename='chat')

urlpatterns = [
    path('', include(router.urls)),
    path('whatsapp/webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('palmpay/create_virtual_account/', CreateVirtualAccountAPIView.as_view(), name='create_virtual_account'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
