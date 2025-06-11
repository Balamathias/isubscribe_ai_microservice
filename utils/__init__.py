DATA_MB_PER_NAIRA = 3.414

CASHBACK_VALUE = 0.01

def format_data_amount(amount: float) -> str:
    """
    Format data amount in MB or GB based on the size.
    
    Args:
        amount (float): Amount in MB
        
    Returns:
        str: Formatted string with appropriate unit
    """
    amount = amount * DATA_MB_PER_NAIRA

    if amount <= 1.024:
        return f"{amount:.2f} MB"
    elif 1 < amount <= 1024:
        return f"{amount:.2f} MB"
    else:
        return f"{(amount/1000):.2f} GB"
