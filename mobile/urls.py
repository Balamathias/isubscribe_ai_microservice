from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import WalletAPIView, TransactionHistoryView, LatestTransactionsView, ProcessTransaction

urlpatterns = [
    path("wallets/", WalletAPIView.as_view(), name="wallets"),
    path("transactions/", TransactionHistoryView.as_view(), name="transactions"),
    path("transactions/latest/", LatestTransactionsView.as_view(), name="latest-transactions"),
    path("process-transactions/", ProcessTransaction.as_view(), name="process-transactions"),
]