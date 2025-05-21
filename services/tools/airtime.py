from typing import Dict, Literal
from services.tools import tool
from services.supabase import supabase

from services.plans.airtime import buy_airtime, BuyAirtimeParams
from pytypes.vtpass import VTPassAirtimeTransactionResponse

@tool
def purchase_airtime(user_id: str, network: Literal["glo", "mtn", "airtel", "etisalat"], amount: float) -> Dict:
    """
    Charge the user's account and purchase airtime.

    Args:
        user_id: Unique identifier of the user.
        network: Name of the network provider.
        amount: Amount of airtime to purchase.

    Returns:
        A dict containing transaction details: tx_id, status, new_balance.
    """
    try:
        tx_resp = supabase.table('history') \
                          .insert({
                              'user_id': user_id,
                              'network': network,
                              'amount': amount,
                              'type': 'airtime_topup',
                              'status': 'pending',
                          }).execute()
        tx = tx_resp.data[0]
    except Exception as e:
        raise Exception(f"Transaction creation failed: {e}")

    try:
        airtime_resp = buy_airtime(
            request_id=tx['id'],
            serviceID=network,
            phone=user_id,
            amount=amount
        )
        if not airtime_resp:
            raise Exception("Airtime purchase failed.")
        code = airtime_resp.get('code')

        if code == '000':
            supabase.rpc('modify_wallet_balance', {'user_id': user_id, 'amount': -amount}).execute()
        else:
            supabase.table('history') \
                    .update({'status': 'failed'}) \
                    .eq('id', tx['id']) \
                    .execute()
            raise Exception(f"Airtime purchase failed: {airtime_resp.get('message')}")

    except Exception as e:
        supabase.table('history') \
                .update({'status': 'failed'}) \
                .eq('id', tx['id']) \
                .execute()
        raise Exception(f"Balance deduction failed: {e}")

    supabase.table('history') \
            .update({'status': 'success'}) \
            .eq('id', tx['id']) \
            .execute()
    
    # Fetch new balance
    # This is a placeholder. Replace with actual balance fetching logic.
    try:
        wallet = supabase.table('wallet') \
                               .select('balance') \
                               .eq('user_id', user_id) \
                               .single() \
                               .execute()
        new_balance = wallet.data.get('balance') if wallet.data else None
    except Exception:
        new_balance = None

    return {
        'tx_id': tx['id'],
        'status': 'success',
        'amount': amount,
        'new_balance': new_balance,
    }
