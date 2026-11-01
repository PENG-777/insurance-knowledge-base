from sqlalchemy.orm import Session

from models import AuditLog


def ok(data=None, msg: str = "success") -> dict:
    return {"code": 0, "data": data, "msg": msg}


def add_audit(
    db: Session,
    actor: str,
    action: str,
    target_type: str = "",
    target_id: int | None = None,
    detail: dict | None = None,
    commit: bool = True,
) -> None:
    db.add(
        AuditLog(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail or {},
        )
    )
    if commit:
        db.commit()
