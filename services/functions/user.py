from core.thread_local import get_current_user
from services.supabase import supabase
from core.context import AgentContext

# get_user_info_declaration = {
#     "name": "get_user_info",
#     "description": "Retrieves user details including phone, email, wallet balance, cashback balance, first name, and last name.",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "user_id": {
#                 "type": "string",
#                 "description": "The user ID whose information is to be retrieved."
#             }
#         }
#     }
# }

def get_user_info() -> dict:
    """
    Fetches user information including wallet balance and cashback balance in Naira (₦).
    Returns:
        A dictionary containing user information or an error message.
    """
    user = AgentContext.get_current_user()
    print("Fetching user info...", user)

    user_id = user.id if user else None
    try:   
        if not user_id:
            return {"error": "User not found"}
        
        wallet = supabase.table("wallet").select("*").eq("user", str(user_id)).execute()
        print(f"Wallet data: {wallet.data}")

        user_info = {
            "id": user_id,
            "phone": user.phone,
            "email": user.email,
            "wallet_balance": getattr(wallet.data[0], "balance", 0) if wallet.data else 0,
            "cashback_balance": getattr(wallet.data[0], "cashback_balance", 0) if wallet.data else 0,
        }
        return user_info
    
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return {"error": str(e)}