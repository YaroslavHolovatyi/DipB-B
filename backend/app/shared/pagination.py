"""
Cursor + offset pagination helpers.

Most list endpoints will accept ``?limit=&offset=`` for now; chat / activity
feeds will graduate to cursor pagination (``?before=<timestamp>``) once they
exist. Both helpers live here so we don't reinvent them in every router.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    """Standard `?limit=&offset=` query model."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class Page(BaseModel, Generic[T]):
    """Generic paginated envelope."""

    items: list[T]
    total: int
    limit: int
    offset: int

    @classmethod
    def of(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        return cls(items=items, total=total, limit=params.limit, offset=params.offset)
