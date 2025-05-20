from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import WalletView

urlpatterns = [
    path("wallets/", WalletView.as_view(), name="wallets"),
]