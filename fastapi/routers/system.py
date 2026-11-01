from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models import Document, KnowledgeEntity, ReviewTask
from routers.common import ok
from services.llm import llm_service

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
def system_status(db: Session = Depends(get_db)) -> dict:
    pending = db.query(ReviewTask).filter(ReviewTask.status == "pending").count()
    data = llm_service.snapshot()
    data.update(
        {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "documents": db.query(Document).count(),
            "entities": db.query(KnowledgeEntity).count(),
            "pending_reviews": pending,
            "published": db.query(Document).filter(Document.status == "published").count(),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    return ok(data)
