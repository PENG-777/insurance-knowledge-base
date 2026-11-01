from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from models import AuditLog, Document
from routers.common import add_audit, ok
from schemas import RiskCheckRequest, audit_out
from services.risk import check_text

router = APIRouter(prefix="/api/risk", tags=["risk"])
audit_router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.post("/check")
def risk_check(payload: RiskCheckRequest, db: Session = Depends(get_db)) -> dict:
    result = check_text(payload.text)
    add_audit(
        db,
        "当前用户",
        "risk_check",
        "risk",
        None,
        {
            "text": payload.text,
            "hits": result["hits"],
            "blocked": result["blocked"],
            "risk_level": result["risk_level"],
        },
    )
    return ok(result)


def _collect_risk_audits(logs: list[AuditLog]) -> tuple[list[dict], int, dict[str, int]]:
    hits: list[dict] = []
    category_counts: dict[str, int] = {}
    for log in logs:
        if log.action not in ("risk_check", "qa_ask"):
            continue
        for hit in (log.detail or {}).get("hits", []):
            category = hit.get("category", "其他")
            category_counts[category] = category_counts.get(category, 0) + 1
            hits.append(
                {
                    "text": (log.detail or {}).get("text") or (log.detail or {}).get("question", ""),
                    "term": hit.get("term"),
                    "category": category,
                    "level": hit.get("level"),
                    "suggestion": hit.get("suggestion", ""),
                    "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "source": log.action,
                }
            )
    return hits, len(hits), category_counts


@router.get("/overview")
def risk_overview(db: Session = Depends(get_db)) -> dict:
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
    hits, hit_count, category_counts = _collect_risk_audits(logs)
    blocked_questions = []
    for log in logs:
        if log.action != "qa_ask":
            continue
        detail = log.detail or {}
        if detail.get("blocked"):
            categories = sorted({h.get("category", "") for h in detail.get("hits", [])})
            blocked_questions.append(
                {
                    "question": detail.get("question", ""),
                    "categories": categories,
                    "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    docs = db.query(Document).all()
    buckets = [
        {"range": "90-100", "count": sum(1 for d in docs if d.compliance_score >= 90)},
        {"range": "80-89", "count": sum(1 for d in docs if 80 <= d.compliance_score < 90)},
        {"range": "70-79", "count": sum(1 for d in docs if 70 <= d.compliance_score < 80)},
        {"range": "60-69", "count": sum(1 for d in docs if 60 <= d.compliance_score < 70)},
        {"range": "<60", "count": sum(1 for d in docs if 0 < d.compliance_score < 60)},
    ]
    categories = [
        {"name": name, "count": count}
        for name, count in sorted(category_counts.items(), key=lambda x: -x[1])
    ]
    recent_audits = logs[:12]
    return ok(
        {
            "sensitive_hits": hit_count,
            "blocked_questions": len(blocked_questions),
            "blocked_total": len(blocked_questions),
            "blocked_list": blocked_questions[:8],
            "categories": categories,
            "compliance_distribution": buckets,
            "recent_hits": hits[:10],
            "recent_audits": [audit_out(log) for log in recent_audits],
            "checked_total": sum(1 for log in logs if log.action in ("risk_check", "qa_ask")),
        }
    )


@audit_router.get("/logs")
def list_audit_logs(
    limit: int = 30,
    action: str = "",
    target_type: str = "",
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    logs = query.order_by(AuditLog.created_at.desc()).limit(min(100, max(1, limit))).all()
    return ok({"items": [audit_out(log) for log in logs], "total": len(logs)})
