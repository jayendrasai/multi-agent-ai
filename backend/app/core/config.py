import json

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core Application
    app_name: str = "AI Orchestrator"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    allowed_origins: str | list[str] = '["http://localhost:3000"]'
    api_v1_str: str = "/api/v1"
    api_request_timeout: int = 30

    # Database
    postgres_user: str
    postgres_password: str
    postgres_db: str
    db_port: int = 5432
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 5
    db_pool_timeout: int = 30

    # Redis & Celery
    redis_port: int = 6379
    redis_url: str
    redis_max_connections: int = 100
    celery_broker_url: str
    celery_result_backend: str
    celery_task_soft_time_limit: int = 240
    celery_task_time_limit: int = 300

    # LLM Configuration
    llm_api_key: str
    llm_model_name: str
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_request_timeout: int = 60
    llm_max_retries: int = 1

    # External Tools
    searxng_base_url: str = "http://searxng:8080"
    openweather_api_key: str = ""
    tool_timeout: int = 15
    tool_max_retries: int = 5
    search_timeout: int = 10
    search_retry_count: int = 3
    search_circuit_breaker_threshold: int = 5

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60
    circuit_breaker_half_open_calls: int = 1

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_reconnect_max_attempts: int = 10

    # Authentication and result caching
    session_cookie_name: str = "orchestrator_session"
    session_lifetime_seconds: int = 60 * 60 * 24 * 14
    session_cookie_secure: bool = False
    password_min_length: int = 10
    cache_ttl_seconds: int = 60 * 60 * 24
    cache_version: str = "v1"

    # Agent Workflow Constraints
    max_plan_steps: int = 10
    max_feedback_loops: int = 2
    max_validation_loops: int = 1
    max_graph_iterations: int = 30
    quality_threshold: float = 0.7
    workflow_stale_timeout: int = 600

    # Observability
    otel_exporter_endpoint: str = "http://otel-collector:4317"
    otel_service_name: str = "ai-orchestrator"
    prometheus_port: int = 9090

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def parsed_allowed_origins(self) -> list[str]:
        if isinstance(self.allowed_origins, str):
            try:
                return json.loads(self.allowed_origins)
            except json.JSONDecodeError:
                return [self.allowed_origins]
        return self.allowed_origins


def get_settings() -> Settings:
    return Settings()
