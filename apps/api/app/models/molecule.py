from __future__ import annotations

import uuid

from sqlalchemy import JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Molecule(Base):
    __tablename__ = "molecules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    rxnorm_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    atc_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    synonyms: Mapped[list] = mapped_column(JSON, default=list)
