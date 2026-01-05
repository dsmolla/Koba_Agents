class AgentError(Exception):
    """Base class for all agent-related errors."""
    pass

class ProviderNotConnectedError(AgentError):
    """Raised when a user tries to use a tool (like Calendar) but hasn't linked the account."""
    def __init__(self, provider: str):
        message = f"User has not connected {provider} account."
        super().__init__(message)

class TokenExpiredError(AgentError):
    """Raised when a refresh token is invalid or revoked."""
    def __init__(self, provider: str):
        message = f"Connection to {provider} has expired. Please reconnect."
        super().__init__(message)