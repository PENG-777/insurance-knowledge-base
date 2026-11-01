from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from routers.common import add_audit, ok
from schemas import AskRequest
from services.llm import llm_service
from services.retrieval import ANSWER_SYSTEM, mock_answer, rerank, search
from services.risk import check_text, compliance_note

router = APIRouter(prefix="/api/qa", tags=["qa"])

SUGGESTIONS = [
    {"id": 1, "question": "寰宇人生终身寿险的等待期是多久？", "tag": "等待期"},
    {"id": 2, "question": "香港版保单的犹豫期和退保规则如何规定？", "tag": "犹豫期"},
    {"id": 3, "question": "环球守护危疾计划覆盖多少种重大疾病，赔付比例是多少？", "tag": "保障责任"},
    {"id": 4, "question": "海外留学意外险理赔需要准备哪些材料？", "tag": "理赔材料"},
    {"id": 5, "question": "高端医疗计划对既往症如何进行核保？", "tag": "核保规则"},
    {"id": 6, "question": "澳门与香港保单的保全服务有哪些差异？", "tag": "地区规则"},
    {"id": 7, "question": "海外理赔的时效和跨境支付方式是什么？", "tag": "理赔时效"},
    {"id": 8, "question": "分红保单的红利如何计算与领取？", "tag": "分红规则"},
]


def mode_label(mode: str) -> str:
    return "DeepSeek 模型" if mode == "llm" else "本地规则引擎"


@router.get("/suggestions")
def suggestions() -> dict:
    return ok({"items": SUGGESTIONS})


@router.post("/ask")
async def ask(payload: AskRequest, db: Session = Depends(get_db)) -> dict:
    question = payload.question.strip()
    risk = check_text(question)
    hits = risk["hits"]
    mode = llm_service.effective_mode()

    if risk["blocked"]:
        answer = (
            "该问题触发多 Agent 风控拦截：涉及条款篡改、隐私索取等不可受理内容。"
            "知识库仅支持条款查询与合规解读，请通过正规保全、核保或理赔流程办理相关事项。"
        )
        result = {
            "question": question,
            "answer": answer,
            "citations": [],
            "confidence": 0.2,
            "mode": mode,
            "mode_label": mode_label(mode),
            "compliance_note": compliance_note(question, hits),
            "blocked": True,
            "risk_level": risk["risk_level"],
            "risk_hits": hits,
            "latency_ms": 0,
        }
        add_audit(
            db,
            "当前用户",
            "qa_ask",
            "qa",
            None,
            {
                "question": question,
                "blocked": True,
                "hits": hits,
                "mode": mode,
                "confidence": 0.2,
                "citations": [],
            },
        )
        return ok(result)

    results = search(db, question, payload.top_k)
    top, rerank_mode = await rerank(question, results, payload.top_k)
    citations = [
        {
            "doc_id": item["doc_id"],
            "doc_title": item["doc_title"],
            "heading": item["heading"],
            "snippet": item["snippet"],
            "score": item["score"],
            "vector_score": item["vector_score"],
            "keyword_score": item["keyword_score"],
        }
        for item in top
    ]
    confidence = round(min(0.96, 0.52 + (top[0]["score"] if top else 0) * 0.45), 2) if top else 0.35

    answer = mock_answer(question, top)
    mode = llm_service.effective_mode()
    if mode == "llm" and top:
        context = "\n".join(
            f"[{i + 1}]《{item['doc_title']}》{item['heading']}：{item['content'][:520]}"
            for i, item in enumerate(top[: payload.top_k])
        )
        prompt = (
            f"问题：{question}\n\n可用条款上下文：\n{context}\n\n"
            "要求：仅依据上下文作答，返回 JSON：answer（中文，简洁、分点）、confidence（0-1 小数）、"
            "compliance_note（若无合规风险返回空字符串）。"
        )
        generated = await llm_service.chat_json(ANSWER_SYSTEM, prompt)
        if generated and isinstance(generated.get("answer"), str) and generated["answer"].strip():
            answer = generated["answer"].strip()
            try:
                confidence = round(max(0.3, min(0.98, float(generated.get("confidence", confidence)))), 2)
            except (TypeError, ValueError):
                pass
        mode = llm_service.effective_mode()

    note = compliance_note(question, hits)
    add_audit(
        db,
        "当前用户",
        "qa_ask",
        "qa",
        None,
        {
            "question": question,
            "blocked": False,
            "hits": hits,
            "mode": mode,
            "confidence": confidence,
            "citations": [c["doc_title"] for c in citations],
            "rerank": rerank_mode,
        },
    )

    return ok(
        {
            "question": question,
            "answer": answer,
            "citations": citations,
            "confidence": confidence,
            "mode": mode,
            "mode_label": mode_label(mode),
            "compliance_note": note,
            "blocked": False,
            "risk_level": risk["risk_level"],
            "risk_hits": hits,
            "rerank_mode": rerank_mode,
            "latency_ms": 0,
        }
    )
