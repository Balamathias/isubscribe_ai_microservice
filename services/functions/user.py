from core.thread_local import get_current_user
from services.supabase import supabase


def get_user_info() -> dict:
    """
    Get the details of the current user including phone, email, and wallet balance, first name, and last name and cashback balance.

    Returns:
        dict: User details including phone, email, and wallet balance and cashback balance.
    """
    try:   
        user = get_current_user()
        if not user:
            return {"error": "User not found"}
        
        wallet = supabase.table("wallet").select("balance, cashback_balance, profile (*)").eq("user", user.id).single().execute()

        user_info = {
            "id": user.id,
            "phone": wallet.data.profile.phone if wallet.data else 0,
            "email": wallet.data.profile.email if wallet.data else 0,
            "wallet_balance": wallet.data.balance if wallet.data else 0,
            "cashback_balance": wallet.data.cashback_balance if wallet.data else 0,
            "first_name": wallet.data.profile.first_name if wallet.data else 0,
            "last_name": wallet.data.profile.last_name if wallet.data else 0,
        }
        return user_info
    
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return {"error": str(e)}