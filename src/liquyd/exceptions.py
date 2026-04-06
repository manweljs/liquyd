class LiquydError(Exception):
    """Base exception for all Liquyd errors."""


class ConfigurationError(LiquydError):
    """Raised when Liquyd configuration is invalid or incomplete."""


class ClientNotConfiguredError(ConfigurationError):
    """Raised when a requested client is not configured."""


class DefaultClientNotConfiguredError(ConfigurationError):
    """Raised when no default client is available."""


class DocumentDefinitionError(LiquydError):
    """Raised when a document class is defined incorrectly."""


class PropertyDefinitionError(DocumentDefinitionError):
    """Raised when a Property is defined incorrectly."""


class BindingError(LiquydError):
    """Raised when a document cannot be bound to a engine client."""


class QueryError(LiquydError):
    """Raised when a query is invalid or cannot be executed."""
