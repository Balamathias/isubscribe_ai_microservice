from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from services.wallet import get_user_wallet

from utils.response import ResponseMixin


class WalletView(APIView, ResponseMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get user wallet details.
        """
        user = request.user
        wallet = get_user_wallet(user.id)

        if wallet:
            return self.response(wallet, status=status.HTTP_200_OK)
        else:
            return self.response(
                error={"detail": "Wallet not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        