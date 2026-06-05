import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base
import enum


class ProcessingStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    complete = "complete"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus), default=ProcessingStatus.pending
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chunks: Mapped[list["Chunk"]] = relationship("Chunk", back_populates="document", cascade="all, delete")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
