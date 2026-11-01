import json
import re
import time
from datetime import datetime

import httpx

from core.config import settings

COOLDOWN_SECONDS = 60


class LLMService:
    """DeepSeek 客户端。auto 模式下失败自动降级，并缓存失败状态 60 秒。"""

    def __init__(self) -> None:
        self._cooldown_until = 0.0
        self._last_error = ""
        self._last_error_at: datetime | None = None
        self._last_success_at: datetime | None = None
        self._last_tokens = 0
        self.calls = 0
        self.fallbacks = 0

    @property
    def configured(self) -> bool:
        return bool(settings.deepseek_api_key)

    @property
    def configured_mode(self) -> str:
        return (settings.llm_mode or "auto").lower()

    def effective_mode(self) -> str:
        if self.configured_mode == "mock" or not self.configured:
            return "mock"
        if time.time() < self._cooldown_until:
            return "mock"
        return "llm"

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def last_tokens(self) -> int:
        return self._last_tokens

    def _fail(self, message: str) -> None:
        self._last_error = message
        self._last_error_at = datetime.now()
        self._cooldown_until = time.time() + COOLDOWN_SECONDS
        self.fallbacks += 1

    async def chat_json(self, system: str, user: str) -> dict | None:
        """调用模型并要求返回 JSON；不可用或失败时返回 None，由调用方使用本地规则。"""
        if self.effective_mode() != "llm":
            return None
        if not self.configured:
            self._fail("未配置 DEEPSEEK_API_KEY，已使用本地规则引擎。")
            return None

        self.calls += 1
        url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.deepseek_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": 1200,
        }
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                detail = ""
                try:
                    body = resp.json()
                    detail = (body.get("error") or {}).get("message") or ""
                except Exception:
                    detail = resp.text[:160]
                hint = "余额不足，" if resp.status_code == 402 else ""
                self._fail(f"DeepSeek 调用失败：{hint}HTTP {resp.status_code} {detail}".strip())
                return None
            body = resp.json()
            self._last_tokens = int((body.get("usage") or {}).get("total_tokens") or 0)
            self._last_success_at = datetime.now()
            content = body["choices"][0]["message"]["content"]
            match = re.search(r"\{[\s\S]*\}", content or "")
            if not match:
                self._fail("模型返回内容无法解析为 JSON，已降级本地规则。")
                return None
            return json.loads(match.group(0))
        except Exception as exc:  # 网络超时或解析异常均降级
            self._fail(f"DeepSeek 调用异常：{type(exc).__name__}，已降级本地规则。")
            return None

    def snapshot(self) -> dict:
        remaining = max(0, int(self._cooldown_until - time.time()))
        return {
            "configured_mode": self.configured_mode,
            "actual_mode": self.effective_mode(),
            "configured": self.configured,
            "model": settings.deepseek_model,
            "base_url": settings.deepseek_base_url,
            "last_error": self._last_error,
            "last_error_at": self._last_error_at.strftime("%Y-%m-%d %H:%M:%S") if self._last_error_at else None,
            "last_success_at": self._last_success_at.strftime("%Y-%m-%d %H:%M:%S") if self._last_success_at else None,
            "cooldown_remaining": remaining,
            "calls": self.calls,
            "fallbacks": self.fallbacks,
        }


llm_service = LLMService()
