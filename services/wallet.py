from services.supabase import supabase


def get_user_wallet(user: str):
    """
    Fetch user wallets from Supabase by user ID.

    Args:
        user (str): The ID of the user.
    """
    try:
        response = supabase.table("wallets").select("*").eq("user", user).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching user wallet: {e}")
        return None