from typing import List
from services.supabase import supabase


def get_super_plans() -> tuple[(List[dict] | None), (Exception | None)]:
    """
    Get data plans from the "super" category from the database.

    Returns:
        tuple: A tuple containing the data plans and an error if any.
    """
    try:
        data_plans = supabase.table("n3t").select("*").execute()
        if data_plans.data:
            return data_plans.data, None
        else:
            return None, Exception({"message": "No data plans found."})
    except Exception as e:
        return None, e


def get_super_plans_by_service(service_id: str) -> tuple[(List[dict] | None), (Exception | None)]:
    """
    Get data plans from the "super" category by service ID from the database.

    Args:
        service_id (str): The service ID to filter the data plans.

    Returns:
        tuple: A tuple containing the data plans and an error if any.
    """
    try:
        data_plans = (
            supabase.table("n3t")
            .select("*")
            .eq("service_id", service_id)
            .execute()
        )
        if data_plans.data:
            return data_plans.data, None
        else:
            return None, Exception({"message": "No data plans found."})
    except Exception as e:
        return None, e


def get_super_plan_by_id(plan_id: str) -> tuple[(List[dict] | None), (Exception | None)]:
    """
    Get a data plan from the "super" category by plan ID from the database.

    Args:
        plan_id (str): The plan ID to filter the data plans.

    Returns:
        tuple: A tuple containing the data plan and an error if any.
    """
    try:
        data_plans = (
            supabase.table("n3t")
            .select("*")
            .eq("plan_id", plan_id)
            .execute()
        )
        if data_plans.data:
            return data_plans.data, None
        else:
            return None, Exception({"message": "No data plans found."})
    except Exception as e:
        return None, e
    

def filter_super_plans(
        network: str | None,
        plan_type: str | None,
        price: int | None,
) -> tuple[(List[dict] | None), (Exception | None)]:
    """
    Filter data plans from the "super" category based on network, plan type, and price.

    Args:
        network (str | None): The network to filter the data plans.
        plan_type (str | None): The plan type to filter the data plans.
        price (int | None): The price to filter the data plans.

    Returns:
        list: A list of filtered data plans.
    """
    
    try:
        query = supabase.table("n3t").select("*")
        if network:
            query = query.eq("network", network)
        if plan_type:
            query = query.eq("plan_type", plan_type)
        if price:
            query = query.lte("price", price)

        data_plans = query.execute()
        if data_plans.data:
            return data_plans.data, None
        return None, Exception({"message": "No data plans found."})
    except Exception as e:
        return None, e
