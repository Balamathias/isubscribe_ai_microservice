import os
import requests
from typing import Optional, Tuple, Dict, List

from dotenv import load_dotenv
load_dotenv()

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
    

def filter_best_plans(
        network: str | None,
        plan_type: str | None,
        price: int | None,
) -> tuple[(List[dict] | None), (Exception | None)]:
    
    """
    Get data plans from the "best" category by network, plan type, and price from the database.

    Args:
        network (str | None): The network to filter the data plans.
        plan_type (str | None): The plan type to filter the data plans.
        price (int | None): The price to filter the data plans.

    Returns:
        tuple: A tuple containing the data plans and an error if any.
    """
    try:
        query = supabase.table("gsub").select("*")

        if network:
            query = query.eq("network", network)
        if plan_type:
            query = query.eq("plan_type", plan_type)
        if price:
            query = query.lte("price", price)

        data_plans = query.execute()

        if data_plans.data:
            return data_plans.data, None
        else:
            return None, Exception({"message": "No data plans found."})
    except Exception as e:
        return None, e
    


def buy_gsub_data(
    plan: str,
    phone: str,
    request_id: str,
    service_id: str,
) -> Tuple[Optional[Dict], int, bool, Optional[str]]:
    """
    Python counterpart to the JS buyGsubData function.
    Sends a POST request to the GSUB API and returns a tuple:
      (response_data_or_None, status_code, success_flag, error_message_or_None)

    Args:
        plan (str): The plan to buy.
        phone (str): The phone number to buy the plan for.
        request_id (str): The request ID for the transaction.
        service_id (str): The service ID for the transaction.

    Returns:
        tuple: A tuple containing the response data, status code, success flag, and error message if any.
    """
    url = "https://api.gsubz.com/api/pay/"
    api_key = os.getenv("GSUB_API_KEY", "")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "plan": plan,
        "phone": phone,
        "amount": "",
        "api": api_key,
        "requestID": request_id,
        "serviceID": service_id
    }

    try:
        res = requests.post(url, headers=headers, data=data, allow_redirects=True)
        status = res.status_code
        json_body = res.json()
        if not res.ok:
            return json_body, status, False, res.reason
        return json_body, status, True, None
    except Exception as e:
        return None, 500, False, str(e)