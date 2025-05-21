class SupabaseUser:
    def __init__(self, id: str, email: str, phone: str, user_metadata: dict):
        self.id = id
        self.email = email
        self.phone = phone
        self.user_metadata = user_metadata

    def __repr__(self) -> str:
        return f"SupabaseUser(id={self.id}, email={self.email}, phone={self.phone}, user_metadata={self.user_metadata})"
    