from services.supabase import supabase


def get_user_wallet(user_id: str):
    """
    Fetch user wallets from Supabase by user ID.

    Args:
        user_id (str): The ID of the user.

    Returns:
        tuple: (wallet details | None, error | None)
    """
    try:
        response = supabase.table("wallet").select("*").eq("user", user_id).execute()
        if response.data:
            return response.data[0], None
        return None, None
    except Exception as e:
        print(f"Error fetching user wallet: {e}")
        return None, e
    