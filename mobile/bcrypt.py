import bcrypt

def hash_pin(pin: str, salt_rounds: int = 10) -> str:
    """
    Hash a PIN using bcrypt
    
    Args:
        pin: The PIN to hash
        salt_rounds: Number of salt rounds (default: 10)
        
    Returns:
        The hashed PIN
    """
    if isinstance(pin, str):
        pin = pin.encode('utf-8')
        
    salt = bcrypt.gensalt(rounds=salt_rounds)
    hashed = bcrypt.hashpw(pin, salt)
    
    return hashed.decode('utf-8')


def verify_pin(pin: str, hashed_pin: str) -> bool:
    """
    Verify a PIN against its hash
    
    Args:
        pin: The PIN to verify
        hashed_pin: The hashed PIN to check against
        
    Returns:
        True if the PIN matches, False otherwise
    """
    if isinstance(pin, str):
        pin = pin.encode('utf-8')
    if isinstance(hashed_pin, str):
        hashed_pin = hashed_pin.encode('utf-8')
        
    return bcrypt.checkpw(pin, hashed_pin)
