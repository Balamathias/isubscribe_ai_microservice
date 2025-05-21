"""This module provides functions to retrieve data plans from the database."""

from services.plans.best_plans import get_best_plans, get_best_plans_by_service, filter_best_plans
from services.plans.super_plans import get_super_plans, get_super_plans_by_service, filter_super_plans


def get_best_data_plans() -> list[dict]:
    """
    Get data plans from the "best" category from the database.

    Returns:
        list: A list of data plans.
    """
    

    data_plans, error = get_best_plans()
    if error:
        return []
    return data_plans or []


def get_super_data_plans() -> list[dict]:
    """
    Get data plans from the "super" category from the database.

    Returns:
        list: A list of data plans.
    """
    
    data_plans, error = get_super_plans()
    if error:
        return []
    return data_plans or []


def get_best_data_plans_by_service(service_id: str) -> list[dict]:
    """
    Get data plans from the "best" category by service ID from the database.

    Args:
        service_id (str): The service ID to filter the data plans.

    Returns:
        list: A list of data plans.
    """
    
    data_plans, error = get_best_plans_by_service(service_id)
    if error:
        return []
    return data_plans or []


def get_super_data_plans_by_service(service_id: str) -> list[dict]:
    """
    Get data plans from the "super" category by service ID from the database.

    Args:
        service_id (str): The service ID to filter the data plans.

    Returns:
        list: A list of data plans.
    """
    
    data_plans, error = get_super_plans_by_service(service_id)
    if error:
        return []
    return data_plans or []


def filter_best_data_plans(
        network: str,
        plan_type: str,
        plan_category: str,
        price: int,
) -> list[dict]:
    """
    Filter data plans based on network, plan type, and price.

    Args:
        network (str): The network to filter the data plans.
        plan_type (str): The plan type to filter the data plans.
        plan_category (str): The plan category to filter the data plans.
        price (int): The price to filter the data plans.

    Returns:
        list: A list of filtered data plans.
    """
    
    data_plans, error = filter_best_plans(network, plan_type, price)
    if error:
        return []
    return data_plans or []


def filter_super_data_plans(
        network: str,
        plan_type: str,
        price: int,
) -> list[dict]:
    """
    Filter data plans based on network, plan type, and price.

    Args:
        network (str): The network to filter the data plans.
        plan_type (str): The plan type to filter the data plans.
        plan_category (str): The plan category to filter the data plans.
        price (int): The price to filter the data plans.

    Returns:
        list: A list of filtered data plans.
    """
    
    data_plans, error = filter_super_plans(network, plan_type, price)
    if error:
        return []
    return data_plans or []