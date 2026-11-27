import pytest
from fastapi import FastAPI, Request
from pydantic import ValidationError

from exportease.api.deps import check_db
from exportease.config import Settings
from exportease.db.url import to_asyncpg_url


def test_health_is_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["version"] == "dev"  # no GIT_SHA outside a CI-built image


def test_git_sha_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("GIT_SHA", "3f2c1ab")
    settings = Settings(app_env="ci", database_url="postgresql://localhost/db", _env_file=None)
    assert settings.git_sha == "3f2c1ab"


def test_ready_when_database_up(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["checks"]["database"] is True


def test_ready_is_503_when_database_down(client, db_state):
    db_state["up"] = False
    assert client.get("/health").status_code == 200  # alive...
    assert client.get("/ready").status_code == 503  # ...but not ready


async def test_check_db_returns_false_when_query_fails():
    class FailingConnection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            del exc_type, exc_value, traceback
            return False

        async def execute(self, statement):
            del statement
            raise OSError("database unavailable")

    class FailingEngine:
        def connect(self):
            return FailingConnection()

    app = FastAPI()
    app.state.engine = FailingEngine()
    request = Request({"type": "http", "app": app})
    assert await check_db(request) is False


def test_list_documents_paginates(client):
    body = client.get("/v1/documents", params={"limit": 2}).json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_search_filters_records(client):
    r = client.get("/v1/documents", params={"q": "beta"})
    assert [d["id"] for d in r.json()["items"]] == ["002"]


def test_metadata_filter(client):
    r = client.get("/v1/documents", params={"kind": "circular"})
    assert r.json()["total"] == 2
    assert r.json()["filters"] == {"kind": "circular"}


def test_invalid_filter_name_is_400(client):
    r = client.get("/v1/documents", params={"Bad-Key": "x"})
    assert r.status_code == 400
    assert r.headers["content-type"] == "application/problem+json"


def test_get_document_found(client):
    r = client.get("/v1/documents/001")
    assert r.status_code == 200
    assert r.json()["title"] == "Alpha guideline"


def test_missing_document_is_problem_details(client):
    r = client.get("/v1/documents/999")
    assert r.status_code == 404
    assert r.headers["content-type"] == "application/problem+json"
    assert r.json()["request_id"] == r.headers["X-Request-ID"]


def test_bad_limit_is_422_problem(client):
    r = client.get("/v1/documents", params={"limit": 0})
    assert r.status_code == 422
    assert r.json()["errors"][0]["field"] == "query.limit"


def test_personal_chat_returns_fixed_reply_without_answer_model_call(client, llm):
    llm.script = ["personal"]
    response = client.post(
        "/v1/chat",
        json={"message": "When will my pending RoDTEP credit be released?", "stream": False},
    )
    assert response.status_code == 200
    assert response.json()["label"] == "personal"
    assert response.json()["answer"] == (
        "I can't know that from public export-policy documents, "
        "and I can't see your individual case or live status."
    )
    assert llm.calls == 1
    assert llm.seen[0]["messages"][0]["content"] == client.app.state.classifier_prompt


def test_off_topic_chat_returns_fixed_reply_without_answer_model_call(client, llm):
    llm.script = ["off_topic"]
    response = client.post(
        "/v1/chat", json={"message": "Suggest a name for my pet dog.", "stream": False}
    )
    assert response.status_code == 200
    assert response.json()["label"] == "off_topic"
    assert (
        response.json()["answer"] == "I can help with export-policy questions, but not that topic."
    )
    assert llm.calls == 1


def test_request_id_is_echoed(client):
    r = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["X-Request-ID"] == "abc123"


@pytest.mark.parametrize("missing", ["APP_ENV", "DATABASE_URL"])
def test_app_refuses_to_start_without_required_settings(monkeypatch, missing):
    monkeypatch.setenv("APP_ENV", "ci")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
    monkeypatch.delenv(missing)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "postgresql://app@ep-x.neon.tech/neondb?sslmode=require&channel_binding=require",
            "postgresql+asyncpg://app@ep-x.neon.tech/neondb?ssl=require",
        ),
        (
            "postgresql://postgres@localhost:5432/app?sslmode=disable",
            "postgresql+asyncpg://postgres@localhost:5432/app",
        ),
        ("postgres://app@h/db", "postgresql+asyncpg://app@h/db"),
    ],
)
def test_database_url_is_converted_for_asyncpg(raw, expected):
    assert to_asyncpg_url(raw) == expected
