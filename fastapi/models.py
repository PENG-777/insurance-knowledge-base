from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def now() -> datetime:
    return datetime.now()


class Document(Base):
    """保单条款文档。"""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    doc_type: Mapped[str] = mapped_column(String(64), default="保险条款")
    region: Mapped[str] = mapped_column(String(16), default="HK")
    product_name: Mapped[str] = mapped_column(String(160), default="")
    version: Mapped[str] = mapped_column(String(32), default="v1.0")
    effective_date: Mapped[str] = mapped_column(String(32), default="")
    status: Mapped[str] = mapped_column(String(16), default="uploaded")
    current_stage: Mapped[str] = mapped_column(String(32), default="")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    pages: Mapped[int] = mapped_column(Integer, default=0)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    risk_level: Mapped[str] = mapped_column(String(16), default="低")
    compliance_score: Mapped[int] = mapped_column(Integer, default=100)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    file_path: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    sections: Mapped[list["Section"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="Section.order_index"
    )
    entities: Mapped[list["KnowledgeEntity"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    review_tasks: Mapped[list["ReviewTask"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    pipeline_runs: Mapped[list["PipelineRun"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="PipelineRun.id"
    )


class Section(Base):
    """文档章节（结构化轨）。"""

    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    chapter_no: Mapped[str] = mapped_column(String(64), default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    level: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text, default="")
    page_start: Mapped[int] = mapped_column(Integer, default=0)
    page_end: Mapped[int] = mapped_column(Integer, default=0)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    document: Mapped["Document"] = relationship(back_populates="sections")
    entities: Mapped[list["KnowledgeEntity"]] = relationship(back_populates="section")


class KnowledgeEntity(Base):
    """抽取出的寿险知识对象。"""

    __tablename__ = "knowledge_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    section_id: Mapped[int | None] = mapped_column(ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)
    object_type: Mapped[str] = mapped_column(String(64), default="")
    name: Mapped[str] = mapped_column(String(255), default="")
    fields: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    source_text: Mapped[str] = mapped_column(Text, default="")
    implicit_risk: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    document: Mapped["Document"] = relationship(back_populates="entities")
    section: Mapped["Section"] = relationship(back_populates="entities")
    review_tasks: Mapped[list["ReviewTask"]] = relationship(back_populates="entity")


class Chunk(Base):
    """向量轨切片。"""

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    section_id: Mapped[int | None] = mapped_column(ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)
    content: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    embedding: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    document: Mapped["Document"] = relationship(back_populates="chunks")
    section: Mapped["Section"] = relationship()


class ReviewTask(Base):
    """人机协同复核任务。"""

    __tablename__ = "review_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    entity_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=True)
    level: Mapped[str] = mapped_column(String(8), default="P1", index=True)
    trigger_reason: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    assignee: Mapped[str] = mapped_column(String(64), default="待分配")
    note: Mapped[str] = mapped_column(Text, default="")
    corrected_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="review_tasks")
    entity: Mapped["KnowledgeEntity"] = relationship(back_populates="review_tasks")


class PipelineRun(Base):
    """流水线阶段运行记录。"""

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(32), default="")
    stage_name: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(16), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(String(500), default="")
    output: Mapped[dict] = mapped_column(JSON, default=dict)

    document: Mapped["Document"] = relationship(back_populates="pipeline_runs")


class AuditLog(Base):
    """审计日志。"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(64), default="系统")
    action: Mapped[str] = mapped_column(String(64), default="", index=True)
    target_type: Mapped[str] = mapped_column(String(32), default="")
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
