from typing import Dict
from services.tools import tool
from services.supabase import supabase

@tool
def get_user_balance(user_id: str) -> float:
    """
    Return the current balance for the given user.

    Args:
        user_id: Unique identifier of the user.

    Returns:
        The balance amount as a float.
    """
    resp = supabase.table('balances') \
        .select('amount') \
        .eq('user_id', user_id) \
        .single() \
        .execute()
    if resp.error:
        raise Exception(f"Error fetching balance: {resp.error.message}")
    return resp.data.get('amount', 0.0)
