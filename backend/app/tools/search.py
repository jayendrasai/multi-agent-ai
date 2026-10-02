import logging

import httpx
from duckduckgo_search import DDGS
from opentelemetry import trace

from app.core.config import get_settings
from app.core.exceptions import CircuitBreakerOpenError
from app.tools.schemas import SearchResultItem, SearchToolRequest, SearchToolResponse
from app.worker import celery_app

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
settings = get_settings()

# Simple in-memory circuit breaker for demonstration. 
# In a real distributed system, this state should be in Redis.
class CircuitBreaker:
    def __init__(self, threshold: int):
        self.threshold = threshold
        self.failures = 0
        self.is_open = False

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.is_open = True
            
    def record_success(self):
        self.failures = 0
        self.is_open = False

searxng_cb = CircuitBreaker(settings.search_circuit_breaker_threshold) # type: ignore


def _search_searxng(query: str, num_results: int) -> list[SearchResultItem]:
    if searxng_cb.is_open:
        raise CircuitBreakerOpenError("SearXNG circuit breaker is open.")
    
    url = f"{settings.searxng_base_url.rstrip('/')}/search" # type: ignore
    params = {
        "q": query,
        "format": "json",
        "engines": "google,bing,duckduckgo,wikipedia"
    }
    try:
        with httpx.Client(timeout=settings.search_timeout) as client: # type: ignore
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", [])[:num_results]:
                results.append(SearchResultItem(
                    title=item.get("title", ""),
                    link=item.get("url", ""),
                    snippet=item.get("content", "")
                ))
            searxng_cb.record_success()
            return results
    except Exception as e:
        searxng_cb.record_failure()
        logger.warning(f"SearXNG search failed: {e}")
        raise


def _search_duckduckgo(query: str, num_results: int) -> list[SearchResultItem]:
    results = []
    try:
        with DDGS() as ddgs:
            ddg_results = list(ddgs.text(query, max_results=num_results))
            for item in ddg_results:
                results.append(SearchResultItem(
                    title=item.get("title", ""),
                    link=item.get("href", ""),
                    snippet=item.get("body", "")
                ))
        return results
    except Exception as e:
        logger.error(f"DuckDuckGo fallback search failed: {e}")
        raise


def run_search(request_dict: dict) -> dict:
    with tracer.start_as_current_span("execute_search") as span:
        try:
            request = SearchToolRequest(**request_dict)
            span.set_attribute("search.query", request.query)
            last_error = "Search providers unavailable"
            for attempt in range(settings.search_retry_count):
                try:
                    with tracer.start_as_current_span("searxng_request"):
                        results = _search_searxng(request.query, request.num_results)
                    return SearchToolResponse(
                        results=results,
                        provider="searxng",
                        fallback_used=False,
                    ).model_dump()
                except Exception as searx_error:
                    last_error = str(searx_error)
                    span.add_event("searxng_failure", {"attempt": attempt + 1})
                    try:
                        with tracer.start_as_current_span("duckduckgo_fallback_request"):
                            results = _search_duckduckgo(request.query, request.num_results)
                        return SearchToolResponse(
                            results=results,
                            provider="duckduckgo",
                            fallback_used=True,
                        ).model_dump()
                    except Exception as fallback_error:
                        last_error = str(fallback_error)
                        span.add_event("duckduckgo_failure", {"attempt": attempt + 1})
                        logger.warning("Both search providers failed", exc_info=True)

            return SearchToolResponse(
                results=[], provider="none", fallback_used=True, error=last_error
            ).model_dump()
        except Exception as e:
            span.record_exception(e)
            return SearchToolResponse(
                results=[],
                provider="none",
                fallback_used=True,
                error=str(e)
            ).model_dump()


@celery_app.task
def execute_search(request_dict: dict) -> dict:
    return run_search(request_dict)
