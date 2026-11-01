from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from models import Document, KnowledgeEntity, PipelineRun, ReviewTask
from routers.common import ok
from schemas import document_brief, review_out

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

STAGE_NAMES = [
    ("section", "章节识别"),
    ("metadata", "元数据补全"),
    ("extract", "业务内容抽取"),
    ("quality", "增强与质检"),
]


@router.get("/overview")
def overview(db: Session = Depends(get_db)) -> dict:
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    entities = db.query(KnowledgeEntity).count()
    pending = db.query(ReviewTask).filter(ReviewTask.status == "pending").count()
    published = sum(1 for d in docs if d.status == "published")
    processing = sum(1 for d in docs if d.status in ("processing", "uploaded"))
    scores = [d.compliance_score for d in docs]
    compliance_rate = round(sum(scores) / len(scores), 1) if scores else 0.0

    status_distribution = []
    for key, label in (
        ("published", "已发布"),
        ("review", "待复核"),
        ("processing", "处理中"),
        ("uploaded", "待处理"),
        ("failed", "失败"),
    ):
        status_distribution.append(
            {"key": key, "label": label, "count": sum(1 for d in docs if d.status == key)}
        )

    stage_distribution = []
    for stage, name in STAGE_NAMES:
        runs = (
            db.query(PipelineRun)
            .filter(PipelineRun.stage == stage, PipelineRun.status == "success")
            .all()
        )
        doc_ids = {r.document_id for r in runs}
        avg_ms = int(sum(r.duration_ms for r in runs) / len(runs)) if runs else 0
        stage_distribution.append(
            {
                "stage": stage,
                "name": name,
                "count": len(doc_ids),
                "runs": len(runs),
                "avg_duration_ms": avg_ms,
            }
        )

    level_counts = {}
    for level in ("P0", "P1", "P2"):
        level_counts[level] = (
            db.query(ReviewTask)
            .filter(ReviewTask.status == "pending", ReviewTask.level == level)
            .count()
        )

    today = date.today()
    trend = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        day_docs = [d for d in docs if d.created_at and d.created_at.date() == day]
        known = [d for d in docs if d.created_at and d.created_at.date() <= day]
        known_scores = [d.compliance_score for d in known]
        trend.append(
            {
                "date": day.strftime("%m-%d"),
                "documents": len(day_docs),
                "entities": db.query(KnowledgeEntity)
                .filter(
                    KnowledgeEntity.created_at >= datetime.combine(day, datetime.min.time()),
                    KnowledgeEntity.created_at < datetime.combine(day + timedelta(days=1), datetime.min.time()),
                )
                .count(),
                "compliance": round(sum(known_scores) / len(known_scores), 1) if known_scores else 88.0,
            }
        )

    latest = docs[:5]
    pending_tasks = (
        db.query(ReviewTask)
        .filter(ReviewTask.status == "pending")
        .order_by(ReviewTask.level, ReviewTask.created_at.desc())
        .limit(6)
        .all()
    )

    return ok(
        {
            "kpis": {
                "documents": len(docs),
                "entities": entities,
                "pending_reviews": pending,
                "compliance_rate": compliance_rate,
                "published": published,
                "processing": processing,
            },
            "status_distribution": status_distribution,
            "stage_distribution": stage_distribution,
            "review_levels": level_counts,
            "trend": trend,
            "latest_documents": [document_brief(d) for d in latest],
            "review_queue": [review_out(t) for t in pending_tasks],
        }
    )
