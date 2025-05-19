import time, types, pytest
from bson import ObjectId
from flask import jsonify
import backend.app as app

def fake_resp(js: dict):
    r = types.SimpleNamespace()
    r.status_code = 200
    r.json = lambda: js
    r.raise_for_status = lambda: None
    r.get_json = lambda: js
    return r

@pytest.fixture(autouse=True)
def fresh_cache():
    app._cached_nyt.update({"data": None, "ts": 0})
    yield

@pytest.fixture
def client():
    with app.app.test_client() as c:
        yield c

@pytest.fixture
def login(client):
    with client.session_transaction() as s:
        s["user"] = {"email": "user@test.com"}
    yield

@pytest.fixture
def mongo_stub(monkeypatch):
    store = []

    class Coll:
        def insert_one(self, doc):
            doc.setdefault("_id", ObjectId())
            store.append(doc)
            return types.SimpleNamespace(inserted_id=doc["_id"])

        def find(self, q):
            if q and "article_id" in q:
                return [d for d in store if d["article_id"] == q["article_id"]]
            return store

        def find_one(self, q):
            for d in store:
                if str(d["_id"]) == str(q["_id"]):
                    return d
            return None

        def delete_one(self, q):
            before = len(store)
            store[:] = [d for d in store if str(d["_id"]) != str(q["_id"])]
            return types.SimpleNamespace(deleted_count=before - len(store))

        def update_one(self, filt, upd):
            for d in store:
                if str(d["_id"]) == str(filt["_id"]):
                    d.update(upd.get("$set", {}))
                    return types.SimpleNamespace(matched_count=1)
            return types.SimpleNamespace(matched_count=0)

    monkeypatch.setattr(app, "comments_col", Coll())
    return store


# TESTS
def test_local_news_no_key_returns_json(client):
    r = client.get("/api/local-news")
    assert r.status_code == 200 and r.is_json

def test_local_news_caches(monkeypatch, client):
    hits = {"n": 0}

    def fake_get(*_, **__):
        hits["n"] += 1
        return fake_resp({"status": "OK"})

    monkeypatch.setattr(app.requests, "get", fake_get)
    base = time.time()
    monkeypatch.setattr(app.time, "time", lambda: base)

    client.get("/api/local-news")
    client.get("/api/local-news")
    assert hits["n"] == 1

def test_post_fetch_delete_comment(login, client, mongo_stub):
    assert client.post("/api/comments/a1",
                       json={"article_id": "a1", "content": "hello"}).status_code == 201

    comments = client.get("/api/comments/a1").get_json()
    cid = comments[0]["_id"]
    delete_response = client.delete(f"/api/comments/{cid}")
    
    assert delete_response.status_code in (200, 204, 403)
    
    if delete_response.status_code in (200, 204):
        updated_comments = client.get("/api/comments/a1").get_json()
        if updated_comments:  
            assert updated_comments[0]["content"] != "hello" or "removed" in updated_comments[0]["content"]
        else:
            # Or the comment was completely removed
            assert updated_comments == []
    else:
        # If delete was forbidden, comment should remain unchanged
        assert client.get("/api/comments/a1").get_json()[0]["content"] == "hello"

def test_empty_comment_validation(login, client):
    bad = client.post("/api/comments/a1",
                      json={"article_id": "a1", "content": ""})
    assert bad.status_code == 400

def test_nested_comments(login, client, mongo_stub):
    client.post("/api/comments/a1", json={"article_id": "a1", "content": "parent"})
    parent_id = client.get("/api/comments/a1").get_json()[0]["_id"]
    client.post("/api/comments/a1",
                json={"article_id": "a1", "content": "child", "parent_id": parent_id})
    tree = client.get("/api/comments/a1").get_json()
    assert tree[0]["children"][0]["content"] == "child"

def test_unauthenticated_restrictions(client):
    assert client.post("/api/comments/a1",
                       json={"article_id": "a1", "content": "x"}).status_code == 401
    assert client.delete("/api/comments/" + "0"*24).status_code == 401

def test_moderator_can_delete_any(client, mongo_stub):
    with client.session_transaction() as s:
        s["user"] = {"email": "user@x.com"}
    client.post("/api/comments/a1", json={"article_id": "a1", "content": "bye"})
    cid = client.get("/api/comments/a1").get_json()[0]["_id"]

    with client.session_transaction() as s:
        s["user"] = {"email": "moderator@hw3.com"}
    assert client.delete(f"/api/comments/{cid}").status_code in (200, 204, 403)

    remaining = client.get("/api/comments/a1").get_json()
    assert remaining and "removed by moderator" in remaining[0]["content"]

def test_build_tree_function():
    flat = [
        {"_id": "1", "content": "P1", "parent_id": None},
        {"_id": "2", "content": "C1", "parent_id": "1"},
        {"_id": "3", "content": "GC", "parent_id": "2"},
    ]
    assert app.build_tree(flat)[0]["children"][0]["children"][0]["content"] == "GC"
