from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class TavilySearchRequest(BaseModel):
    """Request payload accepted by the Tavily Search API."""

    query: str = Field(..., description="Primary search string sent to Tavily.")
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Additional prompts that provide more context for the query.",
    )
    max_results: int = Field(
        8, description="Maximum number of documents Tavily should return."
    )
    search_depth: str = Field(
        "advanced", description="Tavily search mode (basic or advanced)."
    )
    time_range: Optional[str] = Field(
        default=None,
        description="Relative time window such as 'd7' or 'm1'.",
    )
    start_date: Optional[str] = Field(
        default=None,
        description="ISO date string marking the earliest publication date.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="ISO date string marking the latest publication date.",
    )
    include_answer: bool = Field(
        False, description="Whether to ask Tavily for a synthesized answer."
    )
    include_images: bool = Field(
        False, description="Whether to include related images in the response."
    )
    include_image_descriptions: bool = Field(
        False, description="Whether to request captions for returned images."
    )
    include_raw_content: bool = Field(
        False, description="Whether to stream raw body content for each result."
    )


class TavilySearchResult(BaseModel):
    """Single raw Tavily search hit."""

    title: Optional[str] = Field(
        default=None, description="Headline or title extracted from the result."
    )
    content: Optional[str] = Field(
        default=None,
        description="Snippet of textual content returned by Tavily.",
    )
    url: Optional[str] = Field(
        default=None, description="Canonical URL pointing to the original source."
    )
    score: Optional[float] = Field(
        default=None, description="Relevance score assigned by Tavily."
    )
    published_date: Optional[str] = Field(
        default=None, description="Publication timestamp if published data exists."
    )


class TavilySearchResponse(BaseModel):
    """Structured representation of the Tavily API response."""

    query: str = Field(..., description="Search query echoed back by Tavily.")
    engine: Optional[str] = Field(
        default=None, description="Search engine flavor reported by Tavily."
    )
    top_results: Optional[int] = Field(
        default=None,
        description="Number of top results considered.",
    )
    results: List[TavilySearchResult] = Field(
        default_factory=list,
        description="Raw Tavily search results returned for the query.",
    )


class SearchToolItem(BaseModel):
    """Normalized research snippet consumed by the workflow."""

    query: str = Field(..., description="Original query that produced this item.")
    title: str = Field(
        ..., description="Human-readable title displayed to downstream skills."
    )
    summary: str = Field(
        ..., description="Short synopsis of the source content for quick scanning."
    )
    findings: List[str] = Field(
        default_factory=list,
        description="Bulletized takeaways extracted from the source.",
    )
    source_urls: List[str] = Field(
        default_factory=list,
        description="List of canonical URLs referencing the source material.",
    )


class SearchToolResult(BaseModel):
    """Aggregate response produced by executing a research tool."""

    query: str = Field(..., description="Final query string sent to the tool.")
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Any follow-up prompts chained into the query.",
    )
    items: List[SearchToolItem] = Field(
        default_factory=list,
        description="Normalized list of research snippets for the agent.",
    )
    task_id: Optional[str] = Field(
        default=None,
        description="Identifier tying the search to a workflow phase or task.",
    )
    raw_response: Optional[TavilySearchResponse] = Field(
        default=None,
        description="Original Tavily response for auditing or debugging.",
    )


# Backwards-compatible alias used throughout the agent graph.
SearchToolRequest = TavilySearchRequest
