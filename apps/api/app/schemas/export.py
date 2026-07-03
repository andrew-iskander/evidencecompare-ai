from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

ExportFormat = Literal["pdf", "pptx", "xlsx", "markdown"]


class ExportCreateIn(BaseModel):
    format: ExportFormat


class ExportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    format: str
    status: str
    object_url: str | None = None
    content: str | None = None
