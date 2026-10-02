import hashlib
import logging

import redis.asyncio as redis

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


def build_cache_key(user_id, prompt: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    normalized_prompt = " ".join(prompt.split()).casefold()
    prompt_digest = hashlib.sha256(normalized_prompt.encode("utf-8")).hexdigest()
    return (
        f"workflow-result:{settings.cache_version}:"
        f"{settings.llm_model_name}:{user_id}:{prompt_digest}"
    )


async def get_cached_result(user_id, prompt: str) -> str | None:
    settings = get_settings()
    if settings.cache_ttl_seconds <= 0:
        return None

    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        value = await client.get(build_cache_key(user_id, prompt, settings))
        return value if isinstance(value, str) else None
    except Exception:
        logger.exception("Workflow result cache read failed", extra={"user_id": str(user_id)})
        return None
    finally:
        await client.aclose()


async def set_cached_result(user_id, prompt: str, result: str) -> None:
    settings = get_settings()
    if settings.cache_ttl_seconds <= 0 or not result:
        return

    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.set(
            build_cache_key(user_id, prompt, settings),
            result,
            ex=settings.cache_ttl_seconds,
        )
    except Exception:
        logger.exception("Workflow result cache write failed", extra={"user_id": str(user_id)})
    finally:
        await client.aclose()
