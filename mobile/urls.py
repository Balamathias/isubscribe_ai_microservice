from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import WalletAPIView, TransactionHistoryView, LatestTransactionsView, ProcessTransaction, VerifyPinView, ListDataPlansView

urlpatterns = [
    path("wallets/", WalletAPIView.as_view(), name="wallets"),
    path("transactions/", TransactionHistoryView.as_view(), name="transactions"),
    path("transactions/latest/", LatestTransactionsView.as_view(), name="latest-transactions"),
    path("process-transactions/", ProcessTransaction.as_view(), name="process-transactions"),
    path("verify-pin/", VerifyPinView.as_view(), name="verify-pin"),
    path("list-plans/", ListDataPlansView.as_view(), name="list-plans"),
]