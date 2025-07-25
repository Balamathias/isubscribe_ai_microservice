from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    WalletAPIView, 
    TransactionHistoryView, 
    LatestTransactionsView, 
    ProcessTransaction, 
    VerifyPinView, 
    ListDataPlansView,
    VerifyPhoneNumberView,
    BeneficiariesView,
    ListElectricityView,
    ListTVCableView,
    AppConfig,
    VerifyMerchantView,
    VerifyEducationMerchantView,
    ListEducationServicesView,
    RatingsView,
    DeleteAccountView,
)

urlpatterns = [
    path("wallets/", WalletAPIView.as_view(), name="wallets"),
    path("transactions/", TransactionHistoryView.as_view(), name="transactions"),
    path("transactions/<int:transaction_id>/", TransactionHistoryView.as_view(), name="transaction-detail"),
    path("transactions/latest/", LatestTransactionsView.as_view(), name="latest-transactions"),
    path("process-transactions/", ProcessTransaction.as_view(), name="process-transactions"),
    path("verify-pin/", VerifyPinView.as_view(), name="verify-pin"),
    path("list-plans/", ListDataPlansView.as_view(), name="list-plans"),
    path("verify-phone/", VerifyPhoneNumberView.as_view(), name="verify-phone"),
    path("beneficiaries/", BeneficiariesView.as_view(), name="beneficiaries"),
    path("list-electricity/", ListElectricityView.as_view(), name="list-electricity"),
    path("list-tv/", ListTVCableView.as_view(), name="list-tv"),
    path("app-config/", AppConfig.as_view(), name="app-config"),
    path("verify-merchant/", VerifyMerchantView.as_view(), name="verify-merchant"),
    path("verify-education-merchant/", VerifyEducationMerchantView.as_view(), name="verify-education-merchant"),
    path("list-education/", ListEducationServicesView.as_view(), name="list-education"),
    path("ratings/", RatingsView.as_view(), name="ratings"),
    path("delete-account/", DeleteAccountView.as_view(), name="delete-account"),
]