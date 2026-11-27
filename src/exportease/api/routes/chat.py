"""POST /v1/chat (streaming) and GET /v1/usage (what the model calls cost)."""

import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from exportease.api.deps import GatewayDep, UsageDep
from exportease.llm.classify import classify
from exportease.llm.gateway import LLMResult, LLMUnavailable

router = APIRouter(tags=["chat"])

PROMPT_VERSION = "chat_system_v1"  # the file prompts/chat_system_v1.md
CLASSIFIER_PROMPT_VERSION = "classify_v2"  # best measured router: 20/20 on the current set
PERSONAL_REPLY = (
    "I can't know that from public export-policy documents, "
    "and I can't see your individual case or live status."
)
OFF_TOPIC_REPLY = "I can help with export-policy questions, but not that topic."


def load_prompt(directory: Path, name: str = PROMPT_VERSION) -> str:
    """Read a prompt file. A missing file stops the app at start-up: fail fast."""
    return (directory / f"{name}.md").read_text(encoding="utf-8").strip()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    stream: bool = True

    @field_validator("message")
    @classmethod
    def reject_blank_message(cls, message: str) -> str:
        message = message.strip()
        if not message:
            raise ValueError("message must not be blank")
        return message


def sse(data: dict, event: str = "") -> str:
    """One server-sent event: an optional name, a JSON payload, and a blank line."""
    head = f"event: {event}\n" if event else ""
    return f"{head}data: {json.dumps(data, ensure_ascii=False)}\n\n"


def summary(result: LLMResult) -> dict:
    return {k: v for k, v in asdict(result).items() if k != "text"}


@router.post("/chat")
async def chat(body: ChatRequest, request: Request, gateway: GatewayDep):
    try:
        label, route_result = await classify(
            gateway,
            request.app.state.classifier_prompt,
            CLASSIFIER_PROMPT_VERSION,
            body.message,
        )
    except LLMUnavailable as exc:
        raise HTTPException(
            status_code=503, detail=f"No model could classify this question: {exc}"
        ) from exc

    if label == "invalid":
        raise HTTPException(
            status_code=502, detail="The question router returned an invalid label."
        )
    if label in ("personal", "off_topic"):
        answer = PERSONAL_REPLY if label == "personal" else OFF_TOPIC_REPLY
        result_summary = {"label": label, **summary(route_result)}
        if not body.stream:
            return {"answer": answer, **result_summary}

        async def fixed_events() -> AsyncIterator[str]:
            yield sse({"delta": answer})
            yield sse(result_summary, event="done")

        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        return StreamingResponse(fixed_events(), media_type="text/event-stream", headers=headers)

    messages = [
        {"role": "system", "content": request.app.state.system_prompt},
        {"role": "user", "content": body.message},
    ]
    try:
        if not body.stream:
            result = await gateway.generate(messages, prompt_version=PROMPT_VERSION)
            return {"answer": result.text, **summary(result)}
        stream = gateway.stream(messages, prompt_version=PROMPT_VERSION)
        first = await anext(stream)  # wait for the first piece BEFORE sending status 200
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"No model could answer: {exc}") from exc

    async def events() -> AsyncIterator[str]:
        item: str | LLMResult = first
        try:
            while True:
                if isinstance(item, LLMResult):
                    yield sse(summary(item), event="done")
                    return
                yield sse({"delta": item})
                item = await anext(stream)
        except LLMUnavailable as exc:  # the status line is long gone: say it in the stream
            yield sse({"detail": str(exc)}, event="error")

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(events(), media_type="text/event-stream", headers=headers)


@router.get("/usage")
async def usage(repo: UsageDep, days: Annotated[int, Query(ge=1, le=90)] = 7) -> dict:
    """Tokens and rupees per day, from the llm_calls table."""
    rows = await repo.by_day(days)
    total = round(sum(row["cost_inr"] for row in rows), 4)
    return {"days": rows, "total_cost_inr": total, "calls": sum(row["calls"] for row in rows)}
