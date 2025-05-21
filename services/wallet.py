from typing import Dict, Any, Tuple, Optional, Union
from services.supabase import supabase


def get_user_wallet(user_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[Exception]]:
    """
    Get a user's wallet information from Supabase.

    Args:
        user_id: The user ID to look up

    Returns:
        A tuple containing the wallet data (or None) and an error (or None)
    """
    try:
        response = supabase.table('balances').select('*').eq('user_id', user_id).single().execute()

        if getattr(response, 'error', None):
            return None, Exception(response.error)

        data = getattr(response, 'data', None)
        if not data:
            return None, None

        return data, None
    except Exception as e:
        return None, e


def format_transaction_receipt(tx_data: Dict[str, Any]) -> str:
    """
    Format transaction data as a receipt string.

    Args:
        tx_data: Transaction data dict with keys like tx_id, status, etc.

    Returns:
        A formatted string representation of the transaction receipt
    """
    receipt = ["📝 TRANSACTION RECEIPT"]

    if "tx_id" in tx_data:
        receipt.append(f"Transaction ID: {tx_data['tx_id']}")

    if "status" in tx_data:
        status = tx_data["status"].upper()
        icon = "✅" if status == "COMPLETED" or status == "SUCCESS" else "❌"
        receipt.append(f"Status: {icon} {status}")

    if "amount" in tx_data:
        receipt.append(f"Amount: ₦{tx_data['amount']}")

    if "network" in tx_data:
        receipt.append(f"Network: {tx_data['network'].upper()}")

    if "new_balance" in tx_data:
        receipt.append(f"New Balance: ₦{tx_data['new_balance']}")

    return "\n".join(receipt)
