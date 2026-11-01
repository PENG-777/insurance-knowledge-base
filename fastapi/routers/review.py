from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from models import Document, KnowledgeEntity, ReviewTask
from routers.common import add_audit, ok
from schemas import ResolveRequest, review_out

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/tasks")
def list_tasks(
    level: str = "",
    status: str = "",
    doc_id: int | None = None,
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(ReviewTask)
    if level:
        query = query.filter(ReviewTask.level == level)
    if status:
        query = query.filter(ReviewTask.status == status)
    if doc_id:
        query = query.filter(ReviewTask.document_id == doc_id)
    tasks = query.order_by(ReviewTask.level, ReviewTask.created_at.desc()).all()
    return ok({"items": [review_out(t) for t in tasks], "total": len(tasks)})


@router.get("/stats")
def stats(db: Session = Depends(get_db)) -> dict:
    levels = {}
    for level in ("P0", "P1", "P2"):
        levels[level] = {
            "pending": db.query(ReviewTask)
            .filter(ReviewTask.level == level, ReviewTask.status == "pending")
            .count(),
            "resolved": db.query(ReviewTask)
            .filter(ReviewTask.level == level, ReviewTask.status == "resolved")
            .count(),
        }
    pending_total = sum(item["pending"] for item in levels.values())
    resolved_total = sum(item["resolved"] for item in levels.values())
    resolved = db.query(ReviewTask).filter(ReviewTask.status == "resolved").all()
    today_resolved = sum(1 for t in resolved if t.resolved_at and t.resolved_at.date() == date.today())
    durations = [
        (t.resolved_at - t.created_at).total_seconds() / 60
        for t in resolved
        if t.resolved_at and t.created_at
    ]
    avg_minutes = round(sum(durations) / len(durations), 1) if durations else 0
    waiting_docs = (
        db.query(Document)
        .filter(Document.status == "review")
        .count()
    )
    return ok(
        {
            "levels": levels,
            "pending_total": pending_total,
            "resolved_total": resolved_total,
            "today_resolved": today_resolved,
            "avg_resolution_minutes": avg_minutes,
            "documents_waiting": waiting_docs,
        }
    )


@router.post("/tasks/{task_id}/resolve")
def resolve_task(task_id: int, payload: ResolveRequest, db: Session = Depends(get_db)) -> dict:
    task = db.get(ReviewTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="复核任务不存在")
    if task.status == "resolved":
        raise HTTPException(status_code=400, detail="该任务已完成复核")
    entity = db.get(KnowledgeEntity, task.entity_id) if task.entity_id else None

    if payload.action == "approve" and entity:
        entity.status = "approved"
        if payload.corrected_fields:
            merged = dict(entity.fields or {})
            merged.update(payload.corrected_fields)
            entity.fields = merged
            task.corrected_fields = payload.corrected_fields
    elif entity:
        entity.status = "rejected"

    task.status = "resolved"
    task.note = payload.note or ("复核通过" if payload.action == "approve" else "驳回待修正")
    task.resolved_at = datetime.now()
    if task.assignee == "待分配":
        task.assignee = "陈保怡"
    db.flush()

    doc = db.get(Document, task.document_id)
    if doc:
        remaining = (
            db.query(ReviewTask)
            .filter(
                ReviewTask.document_id == doc.id,
                ReviewTask.status == "pending",
                ReviewTask.level.in_(["P0", "P1"]),
            )
            .count()
        )
        doc.status = "published" if remaining == 0 else "review"
        if doc.status == "published":
            doc.current_stage = "已完成"
            doc.progress = 100
    db.commit()
    db.refresh(task)
    add_audit(
        db,
        "复核员 陈保怡",
        "review_approve" if payload.action == "approve" else "review_reject",
        "review_task",
        task.id,
        {
            "level": task.level,
            "document_id": task.document_id,
            "object_type": entity.object_type if entity else "文档级",
            "note": task.note,
            "corrected_fields": payload.corrected_fields,
        },
    )
    return ok(review_out(task), "复核已提交")
