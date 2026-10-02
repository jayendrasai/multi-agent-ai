import logging

import httpx
from opentelemetry import trace

from app.core.config import get_settings
from app.core.exceptions import CircuitBreakerOpenError
from app.tools.schemas import WeatherToolRequest, WeatherToolResponse
from app.worker import celery_app

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
settings = get_settings()

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

weather_cb = CircuitBreaker(settings.circuit_breaker_failure_threshold)

def _get_weather(location: str) -> dict:
    if weather_cb.is_open:
        raise CircuitBreakerOpenError("Weather circuit breaker is open.")
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": settings.openweather_api_key,
        "units": "metric"
    }
    try:
        with httpx.Client(timeout=settings.tool_timeout) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            weather_cb.record_success()
            return {
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"]
            }
    except Exception as e:
        weather_cb.record_failure()
        logger.error(f"Weather tool failed: {e}")
        raise


def run_weather(request_dict: dict) -> dict:
    with tracer.start_as_current_span("execute_weather") as span:
        try:
            request = WeatherToolRequest(**request_dict)
            span.set_attribute("weather.location", request.location)
            
            data = _get_weather(request.location)
            response = WeatherToolResponse(
                temperature=data["temperature"],
                description=data["description"],
                humidity=data["humidity"]
            )
            return response.model_dump()
        except Exception as e:
            span.record_exception(e)
            return WeatherToolResponse(
                temperature=0.0,
                description="",
                humidity=0,
                error="Weather service unavailable",
            ).model_dump()


@celery_app.task
def execute_weather(request_dict: dict) -> dict:
    return run_weather(request_dict)
