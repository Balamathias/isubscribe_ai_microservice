from services.supabase import supabase


def get_user_by_phone(phone: str):
    """
    Fetch user details from Supabase by phone number.

    Args:
        phone (str): The phone number of the user.

    Returns:
        tuple: (user details | None, error | None)
    """
    try:
        response = supabase.table("profile").select("*").eq("phone", phone).execute()
        if response.data:
            return response.data[0], None
        return None, None
    except Exception as e:
        print(f"Error fetching user by phone: {e}")
        return None, e
    

def get_user_by_email(email: str):
    """
    Fetch user details from Supabase by email.

    Args:
        email (str): The email of the user.

    Returns:
        tuple: (user details | None, error | None)
    """
    try:
        response = supabase.table("profile").select("*").eq("email", email).execute()
        if response.data:
            return response.data[0], None
        return None, None
    except Exception as e:
        print(f"Error fetching user by email: {e}")
        return None, e
    