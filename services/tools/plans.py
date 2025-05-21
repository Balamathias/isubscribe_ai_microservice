from typing import List, Dict
from services.tools import tool
from services.supabase import supabase

from plans.best_plans import get_best_plans
from plans.super_plans import get_super_plans

@tool
def list_best_data_plans(network: str) -> List[Dict]:
    """
    Return a list of 'best' data plans available for the specified network.

    Each plan object contains:
      - id: unique plan identifier
      - name: plan name
      - price: cost of the plan
      - data_mb: data volume in megabytes
    """
    plans, error = get_best_plans()
    if error:
        raise Exception(f"Error fetching best data plans: {error}")
    if not plans:
        return []
    
    filtered_plans = [
        plan for plan in plans if plan.get('network') == network
    ]
    return [{
        'id': plan.get('id'),
        'name': plan.get('name'),
        'price': plan.get('price'),
        'amount': plan.get('amount'),
    } for plan in filtered_plans]

@tool
def list_super_data_plans(network: str) -> List[Dict]:
    """
    Return a list of 'super' data plans available for the specified network.

    Each plan object contains:
      - id: unique plan identifier
      - name: plan name
      - price: cost of the plan
      - amount: data volume in megabytes
      - duration: validity period in days
    """
    plans, error = get_super_plans()
    if error:
        raise Exception(f"Error fetching super data plans: {error}")
    if not plans:
        return []
    
    filtered_plans = [
        plan for plan in plans if plan.get('network') == network
    ]
    return [{
        'id': plan.get('id'),
        'name': plan.get('name'),
        'price': plan.get('price'),
        'amount': plan.get('amount'),
        'duration': plan.get('duration'),
    } for plan in filtered_plans]

@tool
def purchase_data_plan(user_id: str, plan_id: str) -> Dict:
    """
    Purchase a data plan for a user by plan ID.

    Steps:
      1. Retrieve plan details (price, data_mb, validity_days).
      2. Check user balance and deduct price.
      3. Record transaction in 'telecom_transactions' table.

    Returns:
      A dict containing transaction details: tx_id, status, new_balance.
    """
    # Fetch plan
    plan_resp = supabase.table('best_data_plans').select('*').or_(
        f"id.eq.{plan_id},id.eq.{plan_id}"  # both tables, best or super
    ).execute()
    if plan_resp.error or not plan_resp.data:
        raise Exception("Data plan not found.")
    plan = plan_resp.data[0]

    # Create transaction
    tx_payload = {
        'user_id': user_id,
        'network': plan.get('network'),
        'amount': plan.get('price'),
        'type': 'data_purchase',
        'plan_id': plan_id,
        'status': 'pending'
    }
    tx_resp = supabase.table('telecom_transactions').insert(tx_payload).execute()
    if tx_resp.error:
        raise Exception(f"Transaction creation failed: {tx_resp.error.message}")
    tx = tx_resp.data[0]

    # Deduct balance
    rpc = supabase.rpc('deduct_balance', {'user_id': user_id, 'amount': plan.get('price')}).execute()
    if rpc.error:
        supabase.table('telecom_transactions').update({'status': 'failed'}).eq('id', tx['id']).execute()
        raise Exception(f"Balance deduction failed: {rpc.error.message}")

    # Mark completed
    supabase.table('telecom_transactions').update({'status': 'completed'}).eq('id', tx['id']).execute()

    # Fetch new balance
    bal_resp = supabase.table('balances').select('amount').eq('user_id', user_id).single().execute()
    new_balance = bal_resp.data.get('amount') if not bal_resp.error else None

    return {
        'tx_id': tx['id'],
        'status': 'completed',
        'new_balance': new_balance,
    }
