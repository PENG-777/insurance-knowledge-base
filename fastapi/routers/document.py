import math
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models import Chunk, Document, KnowledgeEntity, ReviewTask, Section
from routers.common import add_audit, ok
from schemas import chunk_out, document_brief, entity_out, pipeline_out, section_out
from services.parser import parse_file
from services.pipeline import IMPLICIT_LEVEL, run_pipeline

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_SUFFIX = {".pdf", ".txt", ".md"}


def _pending_count(db: Session, doc_id: int) -> int:
    return db.query(ReviewTask).filter(ReviewTask.document_id == doc_id, ReviewTask.status == "pending").count()


@router.get("")
def list_documents(
    status: str = "",
    keyword: str = "",
    region: str = "",
    page: int = 1,
    pageSize: int = 10,
    db: Session = Depends(get_db),
) -> dict:
    page = max(1, page)
    page_size = min(50, max(1, pageSize))
    query = db.query(Document)
    if status:
        query = query.filter(Document.status == status)
    if region:
        query = query.filter(Document.region == region)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Document.title.like(like),
                Document.filename.like(like),
                Document.product_name.like(like),
                Document.summary.like(like),
            )
        )
    total = query.count()
    docs = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    pending_map = dict(
        db.query(ReviewTask.document_id, func.count(ReviewTask.id))
        .filter(ReviewTask.status == "pending")
        .group_by(ReviewTask.document_id)
        .all()
    )
    return ok(
        {
            "items": [document_brief(d, pending_map.get(d.id, 0)) for d in docs],
            "total": total,
            "page": page,
            "pageSize": page_size,
            "pages": math.ceil(total / page_size) if total else 0,
        }
    )


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(""),
    region: str = Form(""),
    doc_type: str = Form(""),
    product_name: str = Form(""),
    db: Session = Depends(get_db),
) -> dict:
    filename = file.filename or "未命名文档.txt"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIX:
        raise HTTPException(status_code=400, detail="仅支持 PDF、TXT、Markdown 文件")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="文件内容为空")
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    path = settings.upload_path / stored_name
    path.write_bytes(raw)

    try:
        text, pages = parse_file(path, filename)
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"文件解析失败：{exc}") from exc
    if not text.strip():
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="未能从文件中解析出文本内容")

    doc = Document(
        filename=filename,
        title=(title.strip() or Path(filename).stem)[:200],
        doc_type=doc_type.strip() or "保险条款",
        region=(region.strip() or "HK"),
        product_name=product_name.strip(),
        status="uploaded",
        current_stage="等待处理",
        progress=0,
        pages=pages,
        char_count=len(text),
        raw_text=text,
        file_path=str(path),
        risk_level="待评估",
        compliance_score=0,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    add_audit(
        db,
        "当前用户",
        "doc_upload",
        "document",
        doc.id,
        {"filename": filename, "pages": pages, "chars": len(text)},
    )
    background_tasks.add_task(run_pipeline, doc.id, True, 0.35, "上传任务")
    return ok(document_brief(doc), "文件已上传，流水线开始执行")


@router.get("/{doc_id}")
def document_detail(doc_id: int, db: Session = Depends(get_db)) -> dict:
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    sections = db.query(Section).filter(Section.document_id == doc_id).order_by(Section.order_index).all()
    entities = (
        db.query(KnowledgeEntity)
        .filter(KnowledgeEntity.document_id == doc_id)
        .order_by(KnowledgeEntity.object_type, KnowledgeEntity.id)
        .all()
    )
    runs = doc.pipeline_runs
    chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).order_by(Chunk.id).limit(8).all()

    flags = []
    for entity in entities:
        if not entity.implicit_risk:
            continue
        for phrase in (entity.fields or {}).get("模糊表述", []):
            flags.append(
                {
                    "entity_id": entity.id,
                    "object_type": entity.object_type,
                    "section_title": entity.section.title if entity.section else "",
                    "phrase": phrase,
                    "level": IMPLICIT_LEVEL.get(phrase, "P2"),
                }
            )

    data = document_brief(doc, _pending_count(db, doc_id))
    data.update(
        {
            "sections": [section_out(s) for s in sections],
            "entities": [entity_out(e) for e in entities],
            "pipeline_runs": [pipeline_out(r) for r in runs],
            "risk_flags": flags,
            "chunks": {
                "total": db.query(Chunk).filter(Chunk.document_id == doc_id).count(),
                "preview": [chunk_out(c, with_embedding=True) for c in chunks],
            },
        }
    )
    return ok(data)


@router.post("/{doc_id}/run")
def rerun_document(doc_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> dict:
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.status == "processing":
        raise HTTPException(status_code=400, detail="文档正在处理中，请稍后再试")
    doc.status = "processing"
    doc.progress = 1
    doc.current_stage = "等待重新运行"
    db.commit()
    add_audit(db, "当前用户", "doc_rerun", "document", doc.id, {"title": doc.title})
    background_tasks.add_task(run_pipeline, doc.id, True, 0.35, "重新运行任务")
    return ok(document_brief(doc), "已重新提交流水线")


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)) -> dict:
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    title = doc.title
    if doc.file_path:
        Path(doc.file_path).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
    add_audit(db, "当前用户", "doc_delete", "document", doc_id, {"title": title})
    return ok({"id": doc_id}, "文档已删除")
