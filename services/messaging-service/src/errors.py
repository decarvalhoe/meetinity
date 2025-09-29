"""Custom exception hierarchy for the messaging service."""


class MessagingServiceError(Exception):
    """Base error for messaging service operations."""


class AuthenticationError(MessagingServiceError):
    """Raised when the request is not authenticated."""


class AuthorizationError(MessagingServiceError):
    """Raised when a user is not allowed to access a resource."""


class ValidationError(MessagingServiceError):
    """Raised when user input fails validation."""

    def __init__(self, message: str, details: dict[str, list[str]] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConversationExistsError(MessagingServiceError):
    """Raised when attempting to create a duplicate conversation."""


class ConversationNotFoundError(MessagingServiceError):
    """Raised when a conversation cannot be located."""
