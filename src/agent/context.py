from __future__ import annotations

import os

from pydantic import BaseModel, Field


class Context(BaseModel):
    """Runtime context injected when compiling the graph."""

    storage_dir: str | None = Field(
        default=None,
        description="Optional path for persisting finalized checklists.",
    )
    tavily_api_key: str | None = Field(
        default_factory=lambda: os.getenv("TAVILY_API_KEY"),
        description="API key override for Tavily calls.",
    )
    tavily_max_results: int = Field(
        default_factory=lambda: int(os.getenv("TAVILY_MAX_RESULTS", "8")),
        description="Maximum Tavily results to request per search.",
    )
    tavily_search_depth: str = Field(
        default_factory=lambda: os.getenv("TAVILY_SEARCH_DEPTH", "advanced"),
        description="Preferred Tavily search depth (basic or advanced).",
    )
