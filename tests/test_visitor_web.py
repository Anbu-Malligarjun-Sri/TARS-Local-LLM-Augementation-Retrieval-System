import json

from fastapi.testclient import TestClient

from demo.api import WEB, create_app
from demo.dialogue import PROMPTS


URL = "http://visitor.localhost:8091"
HEADERS = {"X-Demo-Client": "1", "Origin": URL}


def test_visitor_asset_allowlist_and_browser_policy():
    with TestClient(create_app(), base_url=URL) as client:
        assert {p.name for p in WEB.iterdir()} == {"visitor.js", "visitor.css", "index.html"}
        page = client.get("/")
        assert page.status_code == 200
        assert "Start visit" in page.text
        assert "connect-src 'self'" in page.headers["Content-Security-Policy"]
        assert "microphone=()" in page.headers["Permissions-Policy"]
        for name in ("visitor.css", "visitor.js"):
            assert client.get("/assets/" + name).status_code == 200
        for path in ("/assets/.env", "/assets/api.py", "/assets/index.html", "/api/media/faces", "/.runtime/memory.sqlite3"):
            assert client.get(path).status_code == 404
        assert not client.cookies


def test_memory_commit_is_scoped_to_a_completed_example_in_a_live_visit():
    app = create_app()
    with TestClient(app, base_url=URL, headers=HEADERS) as a:
        with TestClient(app, base_url=URL, headers=HEADERS) as b:
            a.post("/demo/visit").raise_for_status()
            b.post("/demo/visit").raise_for_status()
            def prepare(client, text, reply_language):
                return client.post("/demo/turns", json={"message": text, "language": reply_language}).json()["id"]

            def reply(client, text, language):
                turn = prepare(client, text, language)
                result = client.post(f"/demo/turns/{turn}/stream")
                result.raise_for_status()
                return "".join(json.loads(row[6:])["content"] for row in result.text.splitlines() if row.startswith("data: "))

            first = prepare(a, PROMPTS["en"][1], "en")
            assert a.get("/demo/visit").json()["active_turn"] == first
            a.post(f"/demo/turns/{first}/stop").raise_for_status()
            assert "haven't" in reply(a, PROMPTS["en"][2], "en")
            reply(a, PROMPTS["en"][1], "ta")
            assert "Un project peru Firefly." in reply(a, PROMPTS["ta"][2], "tanglish")
            assert "haven't" in reply(b, PROMPTS["en"][2], "en")
            assert a.get("/demo/visit").json()["turns_remaining"] == 1
            old_id = a.get("/demo/visit").json()["visit_id"]
            a.delete("/demo/visit").raise_for_status()
            a.post("/demo/visit").raise_for_status()
            assert a.delete("/demo/visit", headers={"X-Demo-Visit": old_id}).status_code == 409
            assert "haven't" in reply(a, PROMPTS["en"][2], "en")
