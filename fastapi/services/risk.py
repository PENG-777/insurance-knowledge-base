"""多 Agent 风控中枢：敏感话题识别与合规提示。"""

SENSITIVE_RULES = [
    {
        "category": "收益承诺",
        "level": "warn",
        "terms": ["保证收益", "保底收益", "稳赚不赔", "稳赚", "零风险", "保本高息", "一定赔付", "必赚"],
        "suggestion": "不得承诺确定收益，请改为基于条款的分红实现率说明，并提示不构成收益保证。",
    },
    {
        "category": "条款篡改",
        "level": "block",
        "terms": ["篡改条款", "修改条款内容", "伪造条款", "规避等待期", "骗保"],
        "suggestion": "涉及篡改或规避条款的请求已拦截，请通过正规保全或核保流程处理。",
    },
    {
        "category": "同业贬低",
        "level": "warn",
        "terms": ["贬低同业", "同行都是骗人", "其他公司都坑", "别家更差"],
        "suggestion": "请避免对同业作贬损性比较，仅陈述本公司条款事实。",
    },
    {
        "category": "隐私索取",
        "level": "block",
        "terms": ["索要隐私", "银行卡密码", "手机验证码", "客户隐私", "身份证照片"],
        "suggestion": "不得索取或传递敏感个人信息，请通过加密合规渠道办理。",
    },
    {
        "category": "免责规避",
        "level": "warn",
        "terms": ["隐瞒免责", "不用告知", "隐瞒病情", "带病投保"],
        "suggestion": "健康告知为合同基础，隐瞒可能导致拒赔，请如实告知。",
    },
    {
        "category": "解释权争议",
        "level": "warn",
        "terms": ["最终解释权"],
        "suggestion": "条款解释应依据合同文本与监管口径，避免单方解释权表述。",
    },
]

COMPLIANCE_TERMS = ["收益", "分红", "回报", "保证", "利率", "irr", "演示", "能不能赔", "一定赔"]
BOUNDARY_TERMS = ["解释", "算不算", "是否属于", "怎么理解", "赔不赔", "条款边界", "争议"]


def check_text(text: str) -> dict:
    hits = []
    lowered = (text or "").lower()
    for rule in SENSITIVE_RULES:
        for term in rule["terms"]:
            if term.lower() in lowered:
                hits.append(
                    {
                        "term": term,
                        "category": rule["category"],
                        "level": rule["level"],
                        "suggestion": rule["suggestion"],
                    }
                )
    categories = sorted({h["category"] for h in hits})
    if any(h["level"] == "block" for h in hits):
        level = "block"
    elif hits:
        level = "warn"
    else:
        level = "safe"
    return {
        "text": text,
        "compliant": not hits,
        "risk_level": level,
        "blocked": level == "block",
        "hits": hits,
        "categories": categories,
        "suggestion": hits[0]["suggestion"] if hits else "未发现敏感话题，可正常处理。",
    }


def compliance_note(question: str, hits: list[dict] | None = None) -> str:
    notes = []
    lowered = (question or "").lower()
    if any(t in lowered for t in COMPLIANCE_TERMS):
        notes.append("本回答仅基于已收录条款文本，不构成收益承诺或投保建议，实际权益以保单合同及监管要求为准。")
    if any(t in lowered for t in BOUNDARY_TERMS):
        notes.append("条款解释存在个案差异，最终应以保险公司核赔结论及合同条款为准。")
    if hits:
        categories = "、".join(sorted({h["category"] for h in hits}))
        notes.append(f"提示：问题命中「{categories}」敏感话题，回答已增加合规约束。")
    return " ".join(notes)
