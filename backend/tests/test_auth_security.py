from uuid import uuid4

from app.auth.security import digest_session_token, hash_password, verify_password
from app.core.config import Settings
from app.workflow.cache import build_cache_key


def test_passwords_are_hashed_and_verified() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_session_digest_is_one_way_stable_hash() -> None:
    token = "test-session-token"

    assert digest_session_token(token) == digest_session_token(token)
    assert digest_session_token(token) != token


def test_cache_key_is_user_scoped_and_prompt_normalized() -> None:
    settings = Settings(
        postgres_user="postgres",
        postgres_password="postgres",
        postgres_db="orchestrator",
        database_url="postgresql+asyncpg://postgres:postgres@db:5432/orchestrator",
        redis_url="redis://redis:6379/0",
        celery_broker_url="redis://redis:6379/1",
        celery_result_backend="redis://redis:6379/2",
        llm_api_key="test-key",
        llm_model_name="test-model",
    )
    user_id = uuid4()

    first = build_cache_key(user_id, "  Hello   World ", settings)
    second = build_cache_key(user_id, "hello world", settings)
    other_user = build_cache_key(uuid4(), "hello world", settings)

    assert first == second
    assert first != other_user
