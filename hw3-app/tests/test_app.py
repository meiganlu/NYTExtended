# tests/test_app.py
import types, time, os
from unittest import mock

import pytest
from flask import json

import backend.app as app


# ────────────────────── helpers ──────────────────────
def _fake_resp(payload, *, status=200):
    """Return an object that mimics requests.Response just enough for app.py"""
    r = types.SimpleNamespace()
    r.status_code = status
    r.json        = lambda: payload
    r.raise_for_status = lambda: None if status == 200 else (_ for _ in ()).throw(RuntimeError)
    return r


# ────────────────────── fixtures ─────────────────────
@pytest.fixture(autouse=True)
def _fresh_env(monkeypatch):
    """Start every test with a clear NYT cache and no API-key."""
    monkeypatch.delenv("NYT_API_KEY", raising=False)
    app._cached_nyt.update({"data": None, "ts": 0})
    yield


@pytest.fixture
def client():
    with app.app.test_client() as c:
        yield c


# ────────────────────── build_tree() ─────────────────
def test_build_tree_minimal():
    flat = [
        {"_id": "1", "content": "root",  "parent_id": None},
        {"_id": "2", "content": "child", "parent_id": "1"},
    ]
    out = app.build_tree(flat)
    assert len(out) == 1 and out[0]["children"][0]["id"] == "2"


# ─────────────── /api/local-news – errors ───────────
def test_local_news_requires_api_key(client):
    """Missing NYT_API_KEY → 500 JSON error payload."""
    resp = client.get("/api/local-news")
    assert resp.status_code == 500
    assert resp.get_json() == {"error": "NYT_API_KEY missing"}


# ───────── /api/local-news – success + cache ────────
def test_local_news_success_and_cache(client, monkeypatch):
    """First call hits NYT; second (within 30 min) served from cache."""
    monkeypatch.setenv("NYT_API_KEY", "dummy-key")

    hits = {"n": 0}

    def fake_get(*a, **k):
        hits["n"] += 1
        return _fake_resp({"status": "OK", "hits": []})

    monkeypatch.setattr(app.requests, "get", fake_get)

    now = time.time()
    monkeypatch.setattr(app.time, "time", lambda: now)        # freeze clock

    r1 = client.get("/api/local-news")
    assert r1.status_code == 200 and hits["n"] == 1

    r2 = client.get("/api/local-news")
    assert r2.status_code == 200 and hits["n"] == 1           # cache hit
    assert r1.get_json() == r2.get_json()
