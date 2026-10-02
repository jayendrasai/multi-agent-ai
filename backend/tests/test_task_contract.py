from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.api.schemas import TaskCreate, TaskResponse
from app.db.models import TaskRun


def test_task_response_reads_persisted_task_fields() -> None:
    task = TaskRun(
        id=uuid4(),
        prompt="Summarize the quarterly report",
        correlation_id=f"corr-{uuid4().hex[:8]}",
        status="PENDING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = TaskResponse.model_validate(task)

    assert response.prompt == task.prompt
    assert response.final_result is None


def test_task_create_rejects_blank_prompts() -> None:
    with pytest.raises(ValidationError):
        TaskCreate(prompt="   ")
