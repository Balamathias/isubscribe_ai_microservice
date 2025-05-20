from typing import List

from services.supabase import supabase


def get_best_plans() -> tuple[(List[dict] | None), (Exception | None)]:
    """
    Get data plans from the "best" category from the database.

    Returns:
        tuple: A tuple containing the data plans and an error if any.
    """
    try:
        data_plans = supabase.table("gsub").select("*").execute()

        if data_plans.data:
            return data_plans.data, None
        else:
            return None, Exception({"message": "No data plans found."})
    except Exception as e:
        return None, e
    

def get_best_plans_by_service(service_id: str) -> tuple[(List[dict] | None), (Exception | None)]:
    """
    Get data plans from the "best" category by service ID from the database.

    Args:
        service_id (str): The service ID to filter the data plans.

    Returns:
        tuple: A tuple containing the data plans and an error if any.
    """
    try:
        data_plans = supabase.table("gsub").select("*").eq("service_id", service_id).execute()

        if data_plans.data:
            return data_plans.data, None
        else:
            return None, Exception({"message": "No data plans found."})
    except Exception as e:
        return None, e
    

def get_best_plan_by_id(plan_id: str) -> tuple[(List[dict] | None), (Exception | None)]:
    """
    Get data plans from the "best" category by plan ID from the database.

    Args:
        plan_id (str): The plan ID to filter the data plans.

    Returns:
        tuple: A tuple containing the data plans and an error if any.
    """
    try:
        data_plans = supabase.table("gsub").select("*").eq("plan_id", plan_id).execute()

        if data_plans.data:
            return data_plans.data, None
        else:
            return None, Exception({"message": "No data plans found."})
    except Exception as e:
        return None, e