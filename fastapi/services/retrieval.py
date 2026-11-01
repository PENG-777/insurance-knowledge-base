"""双轨混合检索：向量余弦 + 关键词覆盖，可选模型精排。"""

import re

from sqlalchemy.orm import Session

from models import Chunk, Document
from services.embedder import HashingEmbedder, bigram_set, cosine
from services.llm import llm_service

ANSWER_SYSTEM = "你是寿险条款知识助手，只依据给定上下文回答，输出严格 JSON。"


def search(db: Session, question: str, top_k: int = 5) -> list[dict]:
    embedder = HashingEmbedder()
    query_vec = embedder.encode(question)
    query_grams = bigram_set(question)
    docs = {d.id: d for d in db.query(Document).all()}
    chunks = db.query(Chunk).all()

    query_keywords = extract_query_keywords(question)
    results = []
    for chunk in chunks:
        doc = docs.get(chunk.document_id)
        if not doc or doc.status not in ("published", "review"):
            continue
        heading = chunk.section.title if chunk.section else ""
        vector_score = cosine(query_vec, chunk.embedding or [])
        content_grams = bigram_set(chunk.content + heading)
        coverage = len(query_grams & content_grams) / len(query_grams) if query_grams else 0.0
        heading_hits = sum(1 for keyword in query_keywords if keyword in heading)
        content_hits = sum(1 for keyword in query_keywords if keyword in chunk.content)
        title_hits = sum(1 for keyword in query_keywords if keyword in doc.title)
        score = min(
            1.0,
            0.5 * vector_score
            + 0.18 * coverage
            + 0.24 * min(1, heading_hits)
            + 0.04 * min(2, content_hits)
            + 0.04 * min(2, title_hits),
        )
        results.append(
            {
                "chunk_id": chunk.id,
                "doc_id": doc.id,
                "doc_title": doc.title,
                "region": doc.region,
                "section_id": chunk.section_id,
                "heading": heading,
                "snippet": _snippet(chunk.content),
                "content": chunk.content,
                "score": round(score, 3),
                "vector_score": round(vector_score, 3),
                "keyword_score": round(coverage, 3),
            }
        )
    results.sort(key=lambda x: -x["score"])
    return results[: max(top_k * 2, top_k)]


def extract_query_keywords(question: str) -> list[str]:
    lexicon = [
        "等待期", "犹豫期", "免责", "责任免除", "理赔", "材料", "时效", "医院", "保费", "费率",
        "保额", "现金价值", "健康告知", "核保", "退保", "分红", "香港", "澳门", "海外", "保全",
        "受益人", "投保年龄", "保险期间", "缴费", "职业", "地区", "重疾", "危疾", "意外",
    ]
    return [word for word in lexicon if word in question]


def _snippet(content: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", content).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


async def rerank(question: str, candidates: list[dict], top_k: int) -> tuple[list[dict], str]:
    """LLM 模式下的轻量精排；不可用时保留加权分数排序。"""
    if len(candidates) <= top_k or llm_service.effective_mode() != "llm":
        return candidates[:top_k], "加权分数"
    brief = "\n".join(
        f"[{i}] {c['doc_title']} / {c['heading']}：{c['snippet'][:100]}" for i, c in enumerate(candidates)
    )
    prompt = (
        "对候选条款按与问题的相关性排序，返回 JSON：ids（仅包含最相关的前 "
        f"{top_k} 个序号）。\n问题：{question}\n候选：\n{brief}"
    )
    result = await llm_service.chat_json(ANSWER_SYSTEM, prompt)
    if result and isinstance(result.get("ids"), list):
        ranked = []
        for idx in result["ids"]:
            if isinstance(idx, int) and 0 <= idx < len(candidates):
                ranked.append(candidates[idx])
        if ranked:
            return ranked[:top_k], "模型精排"
    return candidates[:top_k], "加权分数"


def mock_answer(question: str, results: list[dict]) -> str:
    if not results:
        return (
            "当前知识库中未检索到与该问题直接相关的条款。建议补充上传对应产品条款，"
            "或在复核工作台确认已发布范围后再次提问。"
        )
    top = results[0]
    parts = [f"根据《{top['doc_title']}》{top['heading']}的约定：{top['snippet']}"]
    if len(results) > 1:
        extra = "；".join(f"《{r['doc_title']}》{r['heading']}提到「{r['snippet'][:70]}…」" for r in results[1:3])
        parts.append(f"另可参考：{extra}。")
    parts.append("以上内容以条款原文为准，如需个案结论请提交人工核保或理赔复核。")
    return "".join(parts)
