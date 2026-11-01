"""4 阶段 Agent 抽取流水线：章节识别 → 元数据补全 → 业务内容抽取 → 增强与质检。"""

import asyncio
import hashlib
import re
import time
from datetime import datetime

from core.config import settings
from core.database import SessionLocal
from models import AuditLog, Chunk, Document, KnowledgeEntity, PipelineRun, ReviewTask, Section
from schemas import REGION_LABELS
from services.embedder import HashingEmbedder
from services.llm import llm_service
from services.parser import split_sections
from services.risk import check_text

STAGES = [
    ("section", "章节识别"),
    ("metadata", "元数据补全"),
    ("extract", "业务内容抽取"),
    ("quality", "增强与质检"),
]

REGION_KEYWORDS = [
    ("香港", "HK"),
    ("港版", "HK"),
    ("澳门", "MO"),
    ("澳版", "MO"),
    ("海外", "OVERSEAS"),
    ("留学", "OVERSEAS"),
    ("跨境", "OVERSEAS"),
    ("内地", "CN"),
    ("人民币", "CN"),
]

TYPE_KEYWORDS: dict[str, list[str]] = {
    "产品信息": ["产品名称", "保险产品", "计划名称", "版本", "本产品"],
    "保障责任": ["保障责任", "保险责任", "承保", "给付", "赔付", "保险金"],
    "责任免除": ["责任免除", "免责", "不承担", "不予赔付", "除外责任", "不赔"],
    "等待期": ["等待期", "观察期"],
    "犹豫期": ["犹豫期", "冷静期"],
    "投保年龄": ["投保年龄", "参保年龄", "年龄限制"],
    "保险期间": ["保险期间", "保障期间", "保障期", "终身"],
    "缴费方式": ["缴费方式", "年缴", "月缴", "趸交", "缴费"],
    "保费费率": ["保费", "费率", "保险费"],
    "保额": ["保额", "保险金额", "基本保额"],
    "现金价值": ["现金价值"],
    "理赔材料": ["理赔材料", "索赔资料", "申请材料", "诊断证明", "发票"],
    "理赔时效": ["理赔时效", "赔付时效", "审核时限", "工作日", "自然日"],
    "医院范围": ["指定医院", "医院范围", "医疗机构", "三甲", "私立医院"],
    "地区规则": ["香港", "澳门", "内地", "跨境", "海外", "地区"],
    "职业限制": ["职业类别", "职业限制"],
    "健康告知": ["健康告知", "告知义务", "既往症", "如实告知"],
    "核保规则": ["核保", "加费", "除外承保", "拒保"],
    "保全服务": ["保全", "受益人变更", "保单贷款", "变更"],
    "术语定义": ["释义", "定义", "本条款所称"],
    "退保规则": ["退保", "解除合同"],
    "分红规则": ["分红", "红利"],
}

OBJECT_TYPES = list(TYPE_KEYWORDS.keys())

CRITICAL_TYPES = {"责任免除", "等待期", "理赔材料", "保费费率", "保额", "犹豫期", "保障责任"}
NUMERIC_TYPES = {"保额", "保费费率", "等待期", "犹豫期", "理赔时效", "投保年龄", "保险期间", "缴费方式"}
TYPE_PRIORITY = {"责任免除": 1.4, "等待期": 1.3, "理赔材料": 1.2, "保费费率": 1.2, "犹豫期": 1.1}

IMPLICIT_PATTERNS = [
    ("以本公司最终审核为准", "P1", "审核口径未量化，需补充书面标准"),
    ("最终解释权", "P0", "单方解释权表述存在合规风险"),
    ("按公司规定", "P1", "引用内部规定，缺少公开可核验标准"),
    ("不另行通知", "P1", "变更不另行通知，客户知情权存在缺口"),
    ("另行通知", "P1", "变更依赖另行通知，客户知情权存在缺口"),
    ("以系统为准", "P1", "以系统数据为准，缺少书面口径"),
    ("视情况而定", "P2", "表述模糊，建议补充量化判定标准"),
    ("原则上", "P2", "原则性表述，建议明确例外条件"),
]
IMPLICIT_LEVEL = {p[0]: p[1] for p in IMPLICIT_PATTERNS}

KEYWORD_LEXICON = [
    "保险", "保障", "责任", "免责", "等待期", "犹豫期", "投保", "年龄", "保险期间", "缴费",
    "保费", "费率", "保额", "现金价值", "理赔", "医院", "地区", "职业", "健康告知", "核保",
    "保全", "退保", "分红", "受益人", "保单", "医疗", "重大疾病", "意外", "身故", "全残",
    "美元", "港元", "澳门元", "跨境", "海外", "香港", "澳门", "免赔额", "赔付比例", "诊疗",
]

META_SYSTEM = "你是寿险条款知识工程师，只输出严格 JSON，不要解释。"
EXTRACT_SYSTEM = "你是保险条款信息抽取器，只输出严格 JSON，不要输出任何解释。"


def _confidence(seed: str) -> float:
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()
    value = int(digest[:8], 16)
    return round(0.62 + (value % 3600) / 10000, 2)


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    counts = []
    for term in KEYWORD_LEXICON:
        count = text.count(term)
        if count:
            counts.append((count, term))
    counts.sort(key=lambda x: (-x[0], KEYWORD_LEXICON.index(x[1])))
    return [term for _, term in counts[:limit]]


def detect_region(text: str, title: str) -> str:
    for scope in (title, text):
        for keyword, code in REGION_KEYWORDS:
            if keyword in scope:
                return code
    return "CN"


def infer_doc_type(title: str, text: str) -> str:
    if "核保" in title:
        return "核保规则"
    if "保全" in title:
        return "保全指引"
    if "理赔" in title:
        return "理赔手册"
    if any(k in title for k in ("意外", "留学")):
        return "意外险条款"
    if any(k in title for k in ("危疾", "医疗", "健康")):
        return "健康险条款"
    return "寿险条款"


def rule_metadata(doc: Document) -> dict:
    text = doc.raw_text
    title = doc.title or doc.filename or "未命名文档"
    region = detect_region(text, title)
    effective = ""
    match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if match:
        effective = f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    else:
        match = re.search(r"生效日期[：:\s]*(\d{4}[-\s]\d{1,2}[-\s]\d{1,2})", text)
        if match:
            effective = match.group(1).replace(" ", "-").replace("-0", "-")
    version_match = re.search(r"(?:版本|V|v)\s*([0-9]+\.[0-9]+)", text)
    product = re.sub(r"(?:条款|核保规则|服务指引|操作手册)(?:（[^）]*）)?$", "", title).strip()
    return {
        "title": title,
        "doc_type": infer_doc_type(title, text),
        "region": region,
        "product_name": product,
        "version": f"v{version_match.group(1)}" if version_match else "v1.0",
        "effective_date": effective or "2024-01-01",
        "keywords": extract_keywords(text, 10),
    }


def section_snippet(content: str, keywords: list[str], limit: int = 220) -> str:
    paragraphs = [p.strip() for p in re.split(r"\n|(?<=。)", content) if p.strip()]
    for p in paragraphs:
        if any(k in p for k in keywords):
            return p[:limit]
    return (paragraphs[0] if paragraphs else content.strip())[:limit]


def numeric_values(text: str) -> list[str]:
    patterns = [
        r"[\d,]+(?:\.\d+)?\s*(?:万美元|万美元|美元|港元|港币|澳门元|万元|元)",
        r"\d+\s*(?:个)?(?:工作日|自然日|日|天|个月|年)",
        r"\d+(?:\.\d+)?%",
        r"\d+\s*(?:至|到|-)\s*\d+\s*(?:周岁|岁)",
    ]
    values: list[str] = []
    for pattern in patterns:
        for value in re.findall(pattern, text):
            cleaned = value.strip()
            if cleaned and cleaned not in values:
                values.append(cleaned)
    return values[:8]


def implicit_phrases(text: str) -> list[str]:
    return [phrase for phrase, _, _ in IMPLICIT_PATTERNS if phrase in text]


def highest_level(phrases: list[str]) -> str | None:
    levels = [IMPLICIT_LEVEL.get(p) for p in phrases if IMPLICIT_LEVEL.get(p)]
    if not levels:
        return None
    return sorted(levels)[0]


def select_types(title: str, content: str) -> list[str]:
    scored = []
    for obj_type, words in TYPE_KEYWORDS.items():
        hits = sum(title.count(w) * 2 + content.count(w) for w in words)
        if hits:
            score = hits + TYPE_PRIORITY.get(obj_type, 0)
            scored.append((score, obj_type))
    scored.sort(key=lambda x: (-x[0], list(TYPE_KEYWORDS.keys()).index(x[1])))
    return [t for _, t in scored[:3]]


def chunk_text(content: str, size: int = 420, overlap: int = 60) -> list[str]:
    text = re.sub(r"\n{3,}", "\n\n", content).strip()
    if len(text) <= size:
        return [text] if text else []
    chunks = []
    start = 0
    while start < len(text):
        piece = text[start : start + size]
        if piece.strip():
            chunks.append(piece.strip())
        if start + size >= len(text):
            break
        start += size - overlap
    return chunks


def _audit(db, action: str, target_type: str, target_id: int | None, detail: dict, actor: str = "Agent 流水线") -> None:
    db.add(
        AuditLog(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
    )


def _cleanup(db, document_id: int) -> None:
    db.query(ReviewTask).filter(ReviewTask.document_id == document_id).delete(synchronize_session=False)
    db.query(KnowledgeEntity).filter(KnowledgeEntity.document_id == document_id).delete(synchronize_session=False)
    db.query(Chunk).filter(Chunk.document_id == document_id).delete(synchronize_session=False)
    db.query(Section).filter(Section.document_id == document_id).delete(synchronize_session=False)
    db.query(PipelineRun).filter(PipelineRun.document_id == document_id).delete(synchronize_session=False)
    db.commit()


def _start_stage(db, doc: Document, key: str, name: str, stage_no: int) -> PipelineRun:
    run = PipelineRun(
        document_id=doc.id,
        stage=key,
        stage_name=name,
        status="running",
        started_at=datetime.now(),
        message=f"第 {stage_no}/4 阶段执行中",
    )
    db.add(run)
    doc.current_stage = name
    db.commit()
    db.refresh(run)
    return run


def _finish_stage(
    db,
    doc: Document,
    run: PipelineRun,
    progress: int,
    message: str,
    output: dict,
    tokens: int = 0,
    status: str = "success",
) -> None:
    finished = datetime.now()
    run.finished_at = finished
    run.duration_ms = int((finished - run.started_at).total_seconds() * 1000)
    run.status = status
    run.message = message
    run.output = output
    run.tokens = tokens
    doc.progress = progress
    db.commit()


async def _stage_sections(db, doc: Document) -> dict:
    sections = split_sections(doc.raw_text)
    if not sections:
        raise ValueError("文档无可解析内容，请检查文件编码或内容")
    total_chars = sum(len(s["content"]) for s in sections) or 1
    cursor = 0
    pages = max(1, doc.pages)
    for index, section in enumerate(sections):
        content = section["content"].strip()
        page_start = min(pages, int(pages * cursor / total_chars) + 1)
        cursor += len(content)
        page_end = min(pages, int(pages * cursor / total_chars) + 1)
        db.add(
            Section(
                document_id=doc.id,
                chapter_no=section["chapter_no"],
                title=section["title"],
                level=section["level"],
                content=content,
                page_start=page_start,
                page_end=max(page_start, page_end),
                order_index=index,
            )
        )
    db.commit()
    return {
        "sections": len(sections),
        "headings": [s["title"] for s in sections[:8]],
        "strategy": "标题正则切分" if any(s["chapter_no"] for s in sections) else "段落聚合",
    }


async def _stage_metadata(db, doc: Document, use_llm: bool) -> tuple[dict, str, int]:
    meta = rule_metadata(doc)
    source = "本地规则引擎"
    tokens = 0
    if use_llm and llm_service.effective_mode() == "llm":
        prompt = (
            "抽取文档元数据，返回 JSON，字段为 title, doc_type, region(HK/MO/CN/OVERSEAS), "
            "product_name, version, effective_date(YYYY-MM-DD), keywords(数组，最多8个)。\n"
            f"文件名：{doc.filename}\n标题：{doc.title}\n正文前 3500 字：\n{doc.raw_text[:3500]}"
        )
        result = await llm_service.chat_json(META_SYSTEM, prompt)
        if result:
            for key in ("title", "doc_type", "product_name", "version", "effective_date"):
                if isinstance(result.get(key), str) and result[key].strip():
                    meta[key] = result[key].strip()
            region = str(result.get("region") or "").upper()
            if region in REGION_LABELS:
                meta["region"] = region
            if isinstance(result.get("keywords"), list):
                meta["keywords"] = [str(k) for k in result["keywords"]][:8]
            source = "DeepSeek 模型"
            tokens = llm_service.last_tokens
    doc.title = meta["title"]
    doc.doc_type = meta["doc_type"]
    doc.region = meta["region"]
    doc.product_name = meta["product_name"]
    doc.version = meta["version"]
    doc.effective_date = meta["effective_date"]
    doc.keywords = meta["keywords"]
    db.commit()
    return meta, source, tokens


async def _stage_extract(db, doc: Document, embedder: HashingEmbedder) -> dict:
    sections = db.query(Section).filter(Section.document_id == doc.id).order_by(Section.order_index).all()
    entity_count = 0
    chunk_count = 0
    all_types: set[str] = set()
    confidences: list[float] = []
    region_label = REGION_LABELS.get(doc.region, doc.region)

    for idx, section in enumerate(sections):
        phrases = implicit_phrases(section.content)
        types = select_types(section.title, section.content)
        for position, obj_type in enumerate(types):
            words = TYPE_KEYWORDS[obj_type]
            snippet = section_snippet(section.content, words)
            values = numeric_values(section.content)
            primary = position == 0 and bool(phrases)
            fields = {
                "适用产品": doc.product_name,
                "适用地区": region_label,
                "条款位置": f"{section.chapter_no} {section.title}".strip(),
                "关键数值": values,
                "原文摘录": snippet,
            }
            if primary:
                fields["模糊表述"] = phrases
            confidence = _confidence(f"{doc.id}-{section.id}-{obj_type}-{snippet[:40]}")
            clean_title = re.sub(r"^第.+?[条章]\s*", "", section.title)[:28] or obj_type
            entity = KnowledgeEntity(
                document_id=doc.id,
                section_id=section.id,
                object_type=obj_type,
                name=f"{obj_type}｜{clean_title}",
                fields=fields,
                confidence=confidence,
                status="pending",
                source_text=snippet,
                implicit_risk=primary,
            )
            db.add(entity)
            entity_count += 1
            all_types.add(obj_type)
            confidences.append(confidence)

        if section.title == "前言" or len(section.content) < 60:
            doc.progress = min(80, 55 + int(25 * (idx + 1) / max(1, len(sections))))
            db.commit()
            continue

        for piece in chunk_text(section.content):
            keywords = extract_keywords(piece, 6)
            db.add(
                Chunk(
                    document_id=doc.id,
                    section_id=section.id,
                    content=piece,
                    keywords=keywords,
                    embedding=embedder.encode(piece),
                )
            )
            chunk_count += 1

        if idx % 4 == 0:
            doc.progress = min(80, 55 + int(25 * (idx + 1) / max(1, len(sections))))
            db.commit()
    db.commit()
    avg = round(sum(confidences) / len(confidences), 2) if confidences else 0
    return {
        "entities": entity_count,
        "chunks": chunk_count,
        "object_types": sorted(all_types),
        "avg_confidence": avg,
        "embedding_dim": embedder.dim,
    }


def _grade_entity(entity: KnowledgeEntity) -> tuple[str, str] | None:
    fields = entity.fields or {}
    values = fields.get("关键数值") or []
    phrases = fields.get("模糊表述") or []
    source = entity.source_text or ""
    conf = entity.confidence

    levels = [IMPLICIT_LEVEL[p] for p in phrases if IMPLICIT_LEVEL.get(p)]
    if "P0" in levels:
        return "P0", "原文出现「最终解释权」等单方解释表述，需合规复核"
    if entity.object_type in CRITICAL_TYPES and conf < 0.8:
        return "P0", f"关键字段「{entity.object_type}」置信度偏低（{conf:.2f}），需人工确认"
    if entity.object_type in NUMERIC_TYPES and not values:
        return "P0", f"关键金额/期限/比例缺失，请补录「{entity.object_type}」核心数值"
    if "P1" in levels:
        return "P1", "条款存在「按公司规定/另行通知/以系统为准」等模糊表述"
    if conf < 0.72:
        return "P1", f"抽取置信度偏低（{conf:.2f}），建议对照原文核对"
    if any(word in source for word in ("视情况", "原则上", "酌情", "可能")):
        return "P1", "原文存在歧义表述，建议明确判定条件"
    if "P2" in levels:
        return "P2", "表述不够明确，建议补充量化标准"
    if entity.object_type in {"术语定义", "保全服务", "产品信息"} and conf < 0.9:
        return "P2", "术语或字段命名建议统一，便于跨文档检索"
    return None


async def _stage_quality(db, doc: Document, use_llm: bool) -> dict:
    sections = db.query(Section).filter(Section.document_id == doc.id).order_by(Section.order_index).all()
    entities = db.query(KnowledgeEntity).filter(KnowledgeEntity.document_id == doc.id).all()

    flags = []
    for section in sections:
        phrases = implicit_phrases(section.content)
        if not phrases:
            continue
        for phrase in phrases:
            level = IMPLICIT_LEVEL.get(phrase, "P2")
            reason = next((p[2] for p in IMPLICIT_PATTERNS if p[0] == phrase), "")
            flags.append(
                {
                    "section_id": section.id,
                    "heading": section.title,
                    "chapter_no": section.chapter_no,
                    "phrase": phrase,
                    "level": level,
                    "reason": reason,
                }
            )

    # 实体级复核任务
    task_summary = {"P0": 0, "P1": 0, "P2": 0}
    section_ids_with_entity_flag = set()
    for entity in entities:
        grade = _grade_entity(entity)
        if not grade:
            entity.status = "approved"
            continue
        level, reason = grade
        entity.status = "pending"
        db.add(
            ReviewTask(
                document_id=doc.id,
                entity_id=entity.id,
                level=level,
                trigger_reason=reason,
                status="pending",
                assignee="待分配",
            )
        )
        task_summary[level] += 1
        if entity.implicit_risk:
            section_ids_with_entity_flag.add(entity.section_id)

    # 未被实体覆盖的文档级风险任务
    for flag in flags:
        if flag["section_id"] in section_ids_with_entity_flag:
            continue
        db.add(
            ReviewTask(
                document_id=doc.id,
                entity_id=None,
                level=flag["level"],
                trigger_reason=f"原文出现模糊表述「{flag['phrase']}」：{flag['reason']}",
                status="pending",
                assignee="待分配",
            )
        )
        task_summary[flag["level"]] += 1

    weight = {"P0": 3, "P1": 2, "P2": 1}
    penalty = sum(task_summary[level] * weight[level] for level in weight)
    score = max(50, min(100, 100 - penalty))
    risk_level = "低" if score >= 85 else ("中" if score >= 70 else "高")

    types_count: dict[str, int] = {}
    for entity in entities:
        types_count[entity.object_type] = types_count.get(entity.object_type, 0) + 1
    top_types = sorted(types_count.items(), key=lambda x: -x[1])[:5]

    first_section = next((s.content.strip().replace("\n", " ") for s in sections), "")
    summary = (
        f"{doc.title}共 {len(sections)} 个条款章节，覆盖"
        + "、".join(t for t, _ in top_types)
        + f"等 {len(types_count)} 类寿险知识对象。核心内容：{first_section[:72]}…"
    )[:190]
    keywords = list(dict.fromkeys([t for t, _ in top_types] + extract_keywords(doc.raw_text, 6)))[:10]
    summary_source = "本地规则引擎"

    if use_llm and llm_service.effective_mode() == "llm":
        prompt = (
            "基于条款内容生成知识摘要，返回 JSON：summary（中文100-150字）、keywords（最多8个）。\n"
            f"文档标题：{doc.title}\n正文：\n{doc.raw_text[:3000]}"
        )
        result = await llm_service.chat_json(EXTRACT_SYSTEM, prompt)
        if result and isinstance(result.get("summary"), str):
            summary = result["summary"][:220]
            if isinstance(result.get("keywords"), list):
                keywords = [str(k) for k in result["keywords"]][:10]
            summary_source = "DeepSeek 模型"

    doc.summary = summary
    doc.keywords = keywords
    doc.compliance_score = score
    doc.risk_level = risk_level

    pending_blocks = task_summary["P0"] + task_summary["P1"]
    doc.status = "review" if pending_blocks else "published"
    db.commit()

    return {
        "summary": summary,
        "summary_source": summary_source,
        "keywords": keywords,
        "risk_flags": flags,
        "review_tasks": task_summary,
        "compliance_score": score,
        "risk_level": risk_level,
        "pending_p0_p1": pending_blocks,
    }


async def run_pipeline(
    document_id: int,
    use_llm: bool = True,
    delay: float = 0.0,
    actor: str = "Agent 流水线",
) -> bool:
    """执行完整流水线；异常时落库失败状态，不抛出到后台任务。"""
    db = SessionLocal()
    doc: Document | None = None
    current_run: PipelineRun | None = None
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return False
        _cleanup(db, document_id)
        doc.status = "processing"
        doc.progress = 2
        doc.current_stage = "章节识别"
        doc.summary = ""
        db.commit()
        _audit(db, "pipeline_run", "document", doc.id, {"title": doc.title, "use_llm": use_llm}, actor)
        db.commit()

        # ① 章节识别
        current_run = _start_stage(db, doc, "section", "章节识别", 1)
        await asyncio.sleep(delay)
        output = await _stage_sections(db, doc)
        _finish_stage(
            db,
            doc,
            current_run,
            25,
            f"识别 {output['sections']} 个章节，采用{output['strategy']}",
            output,
            tokens=len(doc.raw_text) // 2,
        )

        # ② 元数据补全
        current_run = _start_stage(db, doc, "metadata", "元数据补全", 2)
        await asyncio.sleep(delay)
        meta, source, tokens = await _stage_metadata(db, doc, use_llm)
        _finish_stage(
            db,
            doc,
            current_run,
            50,
            f"补全 {len(meta)} 项元数据，来源：{source}",
            {"metadata": meta, "source": source},
            tokens=tokens or len(doc.raw_text[:3500]) // 2,
        )

        # ③ 业务内容抽取
        current_run = _start_stage(db, doc, "extract", "业务内容抽取", 3)
        await asyncio.sleep(delay)
        embedder = HashingEmbedder()
        output = await _stage_extract(db, doc, embedder)
        _finish_stage(
            db,
            doc,
            current_run,
            80,
            f"抽取 {output['entities']} 个知识对象、生成 {output['chunks']} 个向量切片",
            output,
            tokens=len(doc.raw_text) * 2,
        )

        # ④ 增强与质检
        current_run = _start_stage(db, doc, "quality", "增强与质检", 4)
        await asyncio.sleep(delay)
        output = await _stage_quality(db, doc, use_llm)
        flags_count = len(output["risk_flags"])
        tasks = output["review_tasks"]
        _finish_stage(
            db,
            doc,
            current_run,
            100,
            f"生成摘要与合规分 {output['compliance_score']}，发现 {flags_count} 条隐式风险，新增复核任务 {sum(tasks.values())} 个",
            output,
            tokens=len(doc.raw_text[:3000]) // 2 if use_llm else 260,
        )

        doc.current_stage = "已完成"
        doc.progress = 100
        db.commit()
        _audit(
            db,
            "doc_publish" if doc.status == "published" else "doc_review",
            "document",
            doc.id,
            {"status": doc.status, "compliance_score": doc.compliance_score, "pending": sum(tasks.values())},
            actor,
        )
        db.commit()
        return True
    except Exception as exc:
        db.rollback()
        try:
            doc = db.get(Document, document_id)
            if doc:
                doc.status = "failed"
                doc.current_stage = "流水线失败"
                doc.summary = f"处理失败：{exc}"
                db.commit()
            if current_run:
                current_run.status = "failed"
                current_run.finished_at = datetime.now()
                current_run.message = f"执行失败：{exc}"
                db.add(
                    AuditLog(
                        actor=actor,
                        action="pipeline_failed",
                        target_type="document",
                        target_id=document_id,
                        detail={"error": str(exc)[:300]},
                    )
                )
                db.commit()
        except Exception:
            db.rollback()
        return False
    finally:
        db.close()


def run_pipeline_sync(document_id: int, use_llm: bool = False, actor: str = "系统") -> bool:
    """同步入口，供脚本或非异步场景调用。"""
    return asyncio.run(run_pipeline(document_id, use_llm=use_llm, delay=0.0, actor=actor))
