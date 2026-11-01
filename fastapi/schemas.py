from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from models import AuditLog, Chunk, Document, KnowledgeEntity, PipelineRun, ReviewTask, Section

REGION_LABELS = {"HK": "香港", "MO": "澳门", "CN": "内地", "OVERSEAS": "海外"}
STATUS_LABELS = {
    "uploaded": "待处理",
    "processing": "处理中",
    "review": "待复核",
    "published": "已发布",
    "failed": "失败",
}


def fmt_dt(value: datetime | None) -> str | None:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


def fmt_day(value: datetime | None) -> str | None:
    return value.strftime("%Y-%m-%d") if value else None


def document_brief(doc: Document, pending_reviews: int = 0) -> dict:
    return {
        "id": doc.id,
        "filename": doc.filename,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "region": doc.region,
        "region_label": REGION_LABELS.get(doc.region, doc.region),
        "product_name": doc.product_name,
        "version": doc.version,
        "effective_date": doc.effective_date,
        "status": doc.status,
        "status_label": STATUS_LABELS.get(doc.status, doc.status),
        "current_stage": doc.current_stage,
        "progress": doc.progress,
        "pages": doc.pages,
        "char_count": doc.char_count,
        "summary": doc.summary,
        "keywords": doc.keywords or [],
        "risk_level": doc.risk_level,
        "compliance_score": doc.compliance_score,
        "pending_reviews": pending_reviews,
        "created_at": fmt_dt(doc.created_at),
        "updated_at": fmt_dt(doc.updated_at),
    }


def section_out(section: Section) -> dict:
    return {
        "id": section.id,
        "document_id": section.document_id,
        "chapter_no": section.chapter_no,
        "title": section.title,
        "level": section.level,
        "content": section.content,
        "page_start": section.page_start,
        "page_end": section.page_end,
        "order_index": section.order_index,
    }


def entity_out(entity: KnowledgeEntity) -> dict:
    return {
        "id": entity.id,
        "document_id": entity.document_id,
        "section_id": entity.section_id,
        "section_title": entity.section.title if entity.section else "",
        "object_type": entity.object_type,
        "name": entity.name,
        "fields": entity.fields or {},
        "confidence": round(entity.confidence, 2),
        "status": entity.status,
        "source_text": entity.source_text,
        "implicit_risk": entity.implicit_risk,
        "created_at": fmt_dt(entity.created_at),
    }


def pipeline_out(run: PipelineRun) -> dict:
    return {
        "id": run.id,
        "stage": run.stage,
        "stage_name": run.stage_name,
        "status": run.status,
        "started_at": fmt_dt(run.started_at),
        "finished_at": fmt_dt(run.finished_at),
        "duration_ms": run.duration_ms,
        "tokens": run.tokens,
        "message": run.message,
        "output": run.output or {},
    }


def chunk_out(chunk: Chunk, with_embedding: bool = False) -> dict:
    data = {
        "id": chunk.id,
        "document_id": chunk.document_id,
        "section_id": chunk.section_id,
        "section_title": chunk.section.title if chunk.section else "",
        "content": chunk.content,
        "keywords": chunk.keywords or [],
    }
    if with_embedding:
        data["embedding_dim"] = len(chunk.embedding or [])
    return data


def review_out(task: ReviewTask) -> dict:
    entity = task.entity
    return {
        "id": task.id,
        "document_id": task.document_id,
        "document_title": task.document.title if task.document else "",
        "entity_id": task.entity_id,
        "object_type": entity.object_type if entity else "文档级",
        "entity_name": entity.name if entity else (task.document.title if task.document else ""),
        "confidence": round(entity.confidence, 2) if entity else None,
        "fields": entity.fields if entity else {},
        "source_text": entity.source_text if entity else "",
        "section_title": entity.section.title if entity and entity.section else "",
        "section_content": entity.section.content if entity and entity.section else "",
        "level": task.level,
        "trigger_reason": task.trigger_reason,
        "status": task.status,
        "assignee": task.assignee,
        "note": task.note,
        "corrected_fields": task.corrected_fields,
        "created_at": fmt_dt(task.created_at),
        "resolved_at": fmt_dt(task.resolved_at),
    }


def audit_out(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "actor": log.actor,
        "action": log.action,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "detail": log.detail or {},
        "created_at": fmt_dt(log.created_at),
    }


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=800)
    top_k: int = Field(default=5, ge=1, le=10)


class RiskCheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class ResolveRequest(BaseModel):
    action: Literal["approve", "reject"]
    note: str = ""
    corrected_fields: dict | None = None
