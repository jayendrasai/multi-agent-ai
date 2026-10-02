import logging

import simpleeval
from opentelemetry import trace

from app.tools.schemas import (
    AnalysisToolRequest,
    AnalysisToolResponse,
    CalculatorToolRequest,
    CalculatorToolResponse,
    FormatterToolRequest,
    FormatterToolResponse,
)
from app.worker import celery_app

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

def run_analysis(request_dict: dict) -> dict:
    request = AnalysisToolRequest(**request_dict)
    result = f"Analyzed {len(str(request.data))} bytes of data using {request.analysis_type} strategy."
    return AnalysisToolResponse(result=result).model_dump()


def run_calculator(request_dict: dict) -> dict:
    request = CalculatorToolRequest(**request_dict)
    result = simpleeval.simple_eval(request.expression)
    return CalculatorToolResponse(result=float(result)).model_dump()


def run_formatter(request_dict: dict) -> dict:
    request = FormatterToolRequest(**request_dict)
    formatted_content = f"--- {request.format_type.upper()} ---\n{request.content}\n--- END ---"
    return FormatterToolResponse(formatted_content=formatted_content).model_dump()


@celery_app.task
def execute_analysis(request_dict: dict) -> dict:
    with tracer.start_as_current_span("execute_analysis") as span:
        try:
            request = AnalysisToolRequest(**request_dict)
            span.set_attribute("analysis.type", request.analysis_type)
            return run_analysis(request_dict)
        except Exception as e:
            span.record_exception(e)
            return AnalysisToolResponse(result=None, error=str(e)).model_dump()


@celery_app.task
def execute_calculator(request_dict: dict) -> dict:
    with tracer.start_as_current_span("execute_calculator") as span:
        try:
            request = CalculatorToolRequest(**request_dict)
            span.set_attribute("calculator.expression", request.expression)
            return run_calculator(request_dict)
        except Exception as e:
            span.record_exception(e)
            return CalculatorToolResponse(result=0.0, error=str(e)).model_dump()


@celery_app.task
def execute_formatter(request_dict: dict) -> dict:
    with tracer.start_as_current_span("execute_formatter") as span:
        try:
            request = FormatterToolRequest(**request_dict)
            span.set_attribute("formatter.format_type", request.format_type)
            return run_formatter(request_dict)
        except Exception as e:
            span.record_exception(e)
            return FormatterToolResponse(formatted_content="", error=str(e)).model_dump()
