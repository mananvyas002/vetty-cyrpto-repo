class ExternalServiceError(Exception):
    """Raised when the cryptocurrency provider cannot fulfill a request."""


class ExternalServiceTimeout(Exception):
    """Raised when the cryptocurrency provider times out."""
