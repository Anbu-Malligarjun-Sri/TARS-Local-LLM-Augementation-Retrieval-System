from fastapi.testclient import TestClient

from demo.api import COOKIE, TTL_SECONDS, create_app


def test_visit_expiry_capacity_and_cookie_isolation():
    now = [10]
    app = create_app(lambda: now[0], capacity=2)
    headers = {"X-Demo-Client": "1"}
    with TestClient(app, base_url="https://visitor.localhost", headers=headers) as a:
        b = TestClient(app, base_url="https://visitor.localhost", headers=headers)
        c = TestClient(app, base_url="https://visitor.localhost", headers=headers)
        first = a.post("/demo/visit")
        assert first.status_code == 201
        cookie = first.headers["set-cookie"].lower()
        assert all(flag in cookie for flag in ["httponly", "secure", "samesite=strict", "path=/demo/"])
        assert first.headers["cache-control"] == "no-store"
        assert b.post("/demo/visit").status_code == 201
        assert c.post("/demo/visit").status_code == 429
        assert a.cookies[COOKIE] != b.cookies[COOKIE]
        assert b.delete("/demo/visit", headers={"Origin":"https://example.invalid"}).status_code == 403
        now[0] += 30
        assert a.post("/demo/visit").json() == {"expires_in_seconds": TTL_SECONDS-30}
        assert a.delete("/demo/visit", params={"id": "a-different-visitor"}).status_code == 204
        assert a.get("/demo/visit").status_code == 401
        assert b.get("/demo/visit").status_code == 200
        assert c.post("/demo/visit").status_code == 201
        now[0] += TTL_SECONDS-30
        assert b.get("/demo/visit").status_code == 401
        assert c.get("/demo/visit").status_code == 200
        b.close()
        c.close()


def test_visitor_service_rejects_cross_origin_writes_and_has_no_owner_routes():
    with TestClient(create_app(), base_url="http://visitor.localhost") as client:
        assert client.post("/demo/visit").status_code == 403
        headers = {"Origin":"https://elsewhere.invalid", "X-Demo-Client":"1"}
        assert client.post("/demo/visit",headers=headers).status_code == 403
        assert client.post("/demo/visit",headers={"Host":"elsewhere.invalid","X-Demo-Client":"1"}).status_code == 400
        for path in ["/api/chat", "/api/settings", "/api/memory", "/api/jobs", "/openapi.json"]:
            assert client.get(path).status_code == 404


def test_restarted_service_cannot_resume_old_visit():
    origin = "http://visitor.localhost"
    with TestClient(create_app(), base_url=origin) as first:
        assert first.post("/demo/visit",headers={"X-Demo-Client":"1"}).status_code == 201
        token = first.cookies[COOKIE]
    with TestClient(create_app(), base_url=origin) as restarted:
        restarted.cookies.set(COOKIE,token)
        assert restarted.get("/demo/visit").status_code == 401
