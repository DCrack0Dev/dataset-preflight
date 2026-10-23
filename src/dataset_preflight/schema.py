"""Pydantic schemas for the public HTTP boundary."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ValidationRequest(BaseModel):
    """Validated request envelope accepted by POST /v1/validate."""

    model_config = ConfigDict(extra="forbid")

    csv: str = Field(min_length=1)
    contract: dict[str, Any]
