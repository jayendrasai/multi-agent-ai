from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    prompt: str = Field(min_length=1, max_length=10_000)

    def model_post_init(self, __context: object) -> None:
        self.prompt = self.prompt.strip()
        if not self.prompt:
            raise ValueError("prompt must not be blank")


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    username: str | None = Field(default=None, min_length=3, max_length=80)
    password: str = Field(min_length=1, max_length=256)

    def model_post_init(self, __context: object) -> None:
        self.name = self.name.strip()
        self.email = self.email.strip().lower()
        if self.username is not None:
            self.username = self.username.strip().lower()
        if not self.name or "@" not in self.email:
            raise ValueError("name and a valid email are required")
        from app.core.config import get_settings

        if len(self.password) < get_settings().password_min_length:
            raise ValueError(
                f"password must be at least {get_settings().password_min_length} characters"
            )


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    display_name: str
    onboarding_completed: bool
    workflow_interest: str | None = None
    team_size: str | None = None
    experience_level: str | None = None
    created_at: datetime


class OnboardingRequest(BaseModel):
    workflow_interest: str = Field(min_length=2, max_length=50)
    team_size: str = Field(min_length=1, max_length=30)
    experience_level: str = Field(min_length=1, max_length=30)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    correlation_id: str
    status: str
    prompt: str
    final_result: str | None = None
    created_at: datetime
    updated_at: datetime


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_run_id: UUID
    correlation_id: str
    event_type: str
    agent_name: str
    payload: dict
    sequence_number: int
    created_at: datetime


class WorkflowNodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_run_id: UUID
    node_type: str
    node_name: str
    status: str
    inputs: dict | list | str | int | float | bool | None = None
    outputs: dict | list | str | int | float | bool | None = None
    retry_count: int
    execution_duration_ms: int | None = None
    parent_node_id: UUID | None = None
    edge_label: str | None = None
    edge_type: str | None = None
    position_x: float | None = None
    position_y: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
