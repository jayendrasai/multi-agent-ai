class OrchestratorException(Exception):
    """Base exception for the application."""
    def __init__(self, message: str, correlation_id: str | None = None):
        super().__init__(message)
        self.message = message
        self.correlation_id = correlation_id


class ToolExecutionError(OrchestratorException):
    """Raised when a tool fails to execute after all retries."""


class CircuitBreakerOpenError(OrchestratorException):
    """Raised when attempting to call a tool while its circuit breaker is open."""


class LLMAPIError(OrchestratorException):
    """Raised when the LLM provider API fails."""


class ConfigurationError(OrchestratorException):
    """Raised when required configuration is missing or invalid."""


class TaskNotFoundError(OrchestratorException):
    """Raised when a requested task run is not found."""
