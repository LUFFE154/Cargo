from __future__ import annotations


class ApplicationError(Exception):
    """Base exception for application-layer failures."""


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""


class ConflictError(ApplicationError):
    """Raised when a resource already exists."""


class NotFoundError(ApplicationError):
    """Raised when a resource cannot be found."""
