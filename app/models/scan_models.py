"""Scan, chunk, signal, finding ORM models."""

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Scan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "scans"

    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    client_request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    chunks: Mapped[list["ScanChunk"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )


class ScanChunk(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "scan_chunks"

    scan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    client_chunk_id: Mapped[str] = mapped_column(String(128), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(64), nullable=False)
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    dependencies_json: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="chunks")
    signals: Mapped[list["StaticSignal"]] = relationship(
        back_populates="chunk", cascade="all, delete-orphan"
    )


class StaticSignal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "static_signals"

    chunk_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scan_chunks.id", ondelete="CASCADE"), nullable=False
    )
    signal_type: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    location_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    chunk: Mapped["ScanChunk"] = relationship(back_populates="signals")


class Finding(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "findings"

    scan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    vulnerability_type: Mapped[str] = mapped_column(String(256), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    fix: Mapped[str | None] = mapped_column(Text, nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="findings")
