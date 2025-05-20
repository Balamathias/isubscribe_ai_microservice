import threading

def get_best_data_plan(
    user_id: str,
    plan_id: str,
    phone_number: str,
    service_id: str,
    price: float,
) -> dict:
    """
    Get the best data plan for a user.
    """
    # Simulate fetching the best data plan
    # In a real-world scenario, this would involve querying a database or an API
    # For demonstration purposes, we'll just return a mock response
    return {
        "user_id": user_id,
        "plan_id": plan_id,
        "phone_number": phone_number,
        "service_id": service_id,
        "price": price,
        "best_plan": {
            "data_limit": "10GB",
            "validity": "30 days",
            "price": price,
        },
    }
    