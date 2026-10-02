import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class TaskRun(Base):
    __tablename__ = "task_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    prompt = Column(String, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    final_result = Column(String, nullable=True)
    correlation_id = Column(String(36), nullable=False, unique=True)
    metadata_payload = Column(JSONB, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    event_sequence_counter = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_task_runs_status_created", "status", "created_at"),
        Index("idx_task_runs_correlation", "correlation_id"),
        Index("idx_task_runs_user_created", "user_id", "created_at"),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(80), nullable=False, unique=True)
    email = Column(String(320), nullable=False, unique=True)
    display_name = Column(String(120), nullable=False)
    password_hash = Column(String(255), nullable=False)
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    workflow_interest = Column(String(50), nullable=True)
    team_size = Column(String(30), nullable=True)
    experience_level = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
    )


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_digest = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_active", "token_digest", "expires_at", "revoked_at"),
    )


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_run_id = Column(UUID(as_uuid=True), ForeignKey("task_runs.id", ondelete="CASCADE"), nullable=False)
    node_type = Column(String(20), nullable=False)
    node_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    inputs = Column(JSONB, nullable=True)
    outputs = Column(JSONB, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    execution_duration_ms = Column(Integer, nullable=True)
    parent_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id", ondelete="SET NULL"), nullable=True)
    edge_label = Column(String(100), nullable=True)
    edge_type = Column(String(20), nullable=True)
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        Index("idx_wfn_task_run", "task_run_id"),
        Index("idx_wfn_task_status", "task_run_id", "status"),
        Index("idx_wfn_parent", "parent_node_id"),
    )


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_run_id = Column(UUID(as_uuid=True), ForeignKey("task_runs.id", ondelete="CASCADE"), nullable=False)
    workflow_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id", ondelete="SET NULL"), nullable=True)
    agent_name = Column(String(50), nullable=False)
    event_type = Column(String(30), nullable=False)
    payload = Column(JSONB, nullable=False)
    correlation_id = Column(String(36), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        UniqueConstraint("task_run_id", "sequence_number", name="uq_task_seq"),
        Index("idx_ae_task_seq", "task_run_id", "sequence_number"),
        Index("idx_ae_correlation", "correlation_id"),
    )


class ToolInvocation(Base):
    __tablename__ = "tool_invocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_run_id = Column(UUID(as_uuid=True), ForeignKey("task_runs.id", ondelete="CASCADE"), nullable=False)
    workflow_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(50), nullable=False)
    input_params = Column(JSONB, nullable=False)
    output_result = Column(JSONB, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    celery_task_id = Column(String(100), nullable=True)
    attempt_number = Column(Integer, nullable=False, default=1)
    execution_duration_ms = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    correlation_id = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_ti_task_run", "task_run_id"),
        Index("idx_ti_celery", "celery_task_id"),
        Index("idx_ti_tool_status", "tool_name", "status"),
    )


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_run_id = Column(UUID(as_uuid=True), ForeignKey("task_runs.id", ondelete="CASCADE"), nullable=False)
    workflow_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id", ondelete="SET NULL"), nullable=True)
    tool_invocation_id = Column(UUID(as_uuid=True), ForeignKey("tool_invocations.id", ondelete="SET NULL"), nullable=True)
    error_type = Column(String(30), nullable=False)
    severity = Column(String(10), nullable=False)
    error_message = Column(String, nullable=False)
    stack_trace = Column(String, nullable=True)
    context_payload = Column(JSONB, nullable=True)
    correlation_id = Column(String(36), nullable=False)
    is_recovered = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        Index("idx_el_task_run", "task_run_id"),
        Index("idx_el_severity", "severity", "created_at"),
    )


class ExecutionMetrics(Base):
    __tablename__ = "execution_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_run_id = Column(UUID(as_uuid=True), ForeignKey("task_runs.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_duration_ms = Column(Integer, nullable=False)
    llm_call_count = Column(Integer, nullable=False, default=0)
    llm_total_tokens = Column(Integer, nullable=False, default=0)
    tool_call_count = Column(Integer, nullable=False, default=0)
    tool_success_count = Column(Integer, nullable=False, default=0)
    tool_failure_count = Column(Integer, nullable=False, default=0)
    agent_transition_count = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    feedback_loop_count = Column(Integer, nullable=False, default=0)
    per_agent_durations = Column(JSONB, nullable=True)
    per_tool_durations = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (
        Index("idx_em_task_run", "task_run_id"),
    )
