"""Domain-specific exceptions for the notification service."""


class NotificationServiceError(Exception):
    """Base error for notification operations."""


class AuthenticationError(NotificationServiceError):
    """Raised when the request is not authenticated."""


class AuthorizationError(NotificationServiceError):
    """Raised when the user cannot access a resource."""


class ValidationError(NotificationServiceError):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: dict[str, list[str]] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotificationNotFoundError(NotificationServiceError):
    """Raised when a notification does not exist."""


class PreferenceNotFoundError(NotificationServiceError):
    """Raised when user preferences could not be located."""
