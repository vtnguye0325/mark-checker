from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_sub: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    picture: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    queries: Mapped[list[Query]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    mark: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    nice_class: Mapped[int] = mapped_column(Integer, nullable=False)
    translation: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    pseudo_mark: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))

    # Stage 1 results.
    label: Mapped[str | None] = mapped_column(Text, nullable=True)
    prob_distinctive: Mapped[float | None] = mapped_column(nullable=True)
    formatted_input: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stage 2 result.
    attributions: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)

    # Stage 3 results.
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship(back_populates="queries")

    __table_args__ = (
        Index(
            "ix_queries_user_id_created_at",
            "user_id",
            text("created_at DESC"),
        ),
    )
