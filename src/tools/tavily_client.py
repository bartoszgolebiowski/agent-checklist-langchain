from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from tavily import TavilyClient

from tools.models import (
    SearchToolItem,
    SearchToolResult,
    TavilySearchRequest,
    TavilySearchResponse,
)


class TavilyToolError(RuntimeError):
    """Raised when the Tavily API request fails."""


@dataclass(slots=True)
class TavilySearchClient:
    """Thin wrapper around the Tavily Search API."""

    api_key: str
    client: TavilyClient = field(init=False)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise TavilyToolError("TAVILY_API_KEY is not configured.")
        self.client = TavilyClient(api_key=self.api_key)

    def search(
        self,
        payload: TavilySearchRequest,
        *,
        task_id: str | None = None,
    ) -> SearchToolResult:
        """Execute a Tavily search request and normalize the response."""

        params = payload.model_dump(exclude_none=True)
        params.pop("follow_up_questions", None)
        if params.get("time_range"):
            params.pop("start_date", None)
            params.pop("end_date", None)
        try:
            data = self.client.search(**params)
        except Exception as exc:  # pragma: no cover - network errors
            raise TavilyToolError("Tavily search failed") from exc

        tavily_response = TavilySearchResponse.model_validate(data)

        items: List[SearchToolItem] = []
        for result in tavily_response.results:
            summary = (result.content or "").strip()
            title = (result.title or payload.query).strip()
            findings: List[str] = []
            if summary:
                findings.append(summary)
            elif title:
                findings.append(title)

            source_urls: List[str] = []
            if result.url:
                source_urls.append(result.url)

            items.append(
                SearchToolItem(
                    query=payload.query,
                    title=title or payload.query,
                    summary=summary or title or payload.query,
                    findings=findings,
                    source_urls=source_urls,
                )
            )

        if not items:
            items.append(
                SearchToolItem(
                    query=payload.query,
                    title=payload.query,
                    summary="No search results returned.",
                    findings=[],
                    source_urls=[],
                )
            )

        return SearchToolResult(
            query=payload.query,
            follow_up_questions=payload.follow_up_questions,
            items=items,
            task_id=task_id,
            raw_response=tavily_response,
        )
