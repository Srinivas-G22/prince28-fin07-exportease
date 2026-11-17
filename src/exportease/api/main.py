import json
import logging
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from exportease.config import get_settings


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


class Citation(BaseModel):
    notice_number: str
    issue_date: str
    section: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    refused: bool = False


def _load_seed_data() -> dict[str, Any]:
    settings = get_settings()
    if not settings.data_file.exists():
        return {"documents": [], "rodtep_rates": []}
    return json.loads(settings.data_file.read_text(encoding="utf-8"))


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    app = FastAPI(
        title="ExportEase",
        description="DGFT Foreign Trade Policy, Amendment & RoDTEP RAG Engine (FIN-07)",
        version="0.1.0",
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "app": settings.app_name,
            "env": settings.app_env,
        }

    @app.get("/v1/documents")
    async def list_documents(
        q: Optional[str] = Query(default=None, description="Filter by keyword in title, notice number, or summary"),
        doc_type: Optional[str] = Query(default=None, description="Filter by doc_type (e.g., FTP_2023, NOTIFICATION)"),
    ) -> dict[str, Any]:
        docs = _load_seed_data().get("documents", [])
        if doc_type:
            docs = [d for d in docs if d.get("doc_type", "").lower() == doc_type.lower()]
        if q:
            needle = q.lower()
            docs = [
                d for d in docs
                if needle in d.get("title", "").lower()
                or needle in d.get("notice_number", "").lower()
                or needle in d.get("summary", "").lower()
            ]
        return {"count": len(docs), "items": docs}

    @app.get("/v1/hs/{hs_code}")
    async def get_hs_dossier(hs_code: str) -> dict[str, Any]:
        cleaned = hs_code.strip()
        if not cleaned.isdigit() or len(cleaned) not in (4, 6, 8):
            raise HTTPException(status_code=400, detail="HS code must be 4, 6, or 8 digits.")

        rates = _load_seed_data().get("rodtep_rates", [])
        matches = [r for r in rates if r.get("hs_code", "").startswith(cleaned)]
        if not matches:
            raise HTTPException(status_code=404, detail=f"No RoDTEP/policy record found for HS code {cleaned}.")
        return matches[0] if len(matches) == 1 else {"hs_prefix": cleaned, "matches": matches}

    @app.post("/v1/ask", response_model=AskResponse)
    async def ask_question(payload: AskRequest) -> AskResponse:
        # Day 1-2 skeleton: returns safe abstention until RAG retriever is wired in Week 3
        return AskResponse(
            answer="I don't know",
            citations=[],
            refused=True,
        )

    return app