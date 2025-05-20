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
        print("Fetching user wallet details...", request.user)
        print("User ID:", request.user.id)

        user = request.user
        wallet, error = get_user_wallet(user.id)

        if wallet:
            return self.response(wallet, status=status.HTTP_200_OK)
        
        if error:
            return self.response(
                message
                =getattr(error, "message", str(error)),
                error={"detail": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        else:
            return self.response(
                message="Wallet not found.",
                error={"detail": "Wallet not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        