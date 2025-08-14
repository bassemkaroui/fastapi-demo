from ulid import ULID

# --- User Errors ---


class UserNotFoundError(Exception):
    def __init__(self, user_id: ULID) -> None:
        self.user_id = user_id

    def __str__(self) -> str:
        return f"User '{self.user_id}' was not found."


# --- API Key Errors ---


class APIKeyBaseError(Exception):
    def __init__(self, api_key_id: str | None = None, owner_id: ULID | None = None):
        self.api_key_id = api_key_id
        self.owner_id = owner_id


class APIKeyNotFoundOrRevokedError(APIKeyBaseError):
    def __str__(self) -> str:
        return f"API key '{self.api_key_id}' was not found or has been revoked for owner '{self.owner_id}'."


class InvalidAPIKeyError(APIKeyBaseError):
    def __str__(self) -> str:
        return f"API key '{self.api_key_id}' is not valid."
