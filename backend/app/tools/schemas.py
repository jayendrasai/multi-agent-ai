from typing import Any

from pydantic import BaseModel, Field


# Search Tool
class SearchToolRequest(BaseModel):
    query: str = Field(..., description="The search query.")
    num_results: int = Field(5, description="Number of results to return.")


class SearchResultItem(BaseModel):
    title: str
    link: str
    snippet: str


class SearchToolResponse(BaseModel):
    results: list[SearchResultItem]
    provider: str
    fallback_used: bool
    error: str | None = None


# Weather Tool
class WeatherToolRequest(BaseModel):
    location: str = Field(..., description="City name or coordinates.")


class WeatherToolResponse(BaseModel):
    temperature: float
    description: str
    humidity: int
    error: str | None = None


# Analysis Tool
class AnalysisToolRequest(BaseModel):
    data: Any = Field(..., description="The data to analyze.")
    analysis_type: str = Field(..., description="Type of analysis to perform.")


class AnalysisToolResponse(BaseModel):
    result: Any
    error: str | None = None


# Calculator Tool
class CalculatorToolRequest(BaseModel):
    expression: str = Field(..., description="Mathematical expression to evaluate.")


class CalculatorToolResponse(BaseModel):
    result: float
    error: str | None = None


# Formatter Tool
class FormatterToolRequest(BaseModel):
    content: str = Field(..., description="Raw content to format.")
    format_type: str = Field("markdown", description="Target format type.")


class FormatterToolResponse(BaseModel):
    formatted_content: str
    error: str | None = None
