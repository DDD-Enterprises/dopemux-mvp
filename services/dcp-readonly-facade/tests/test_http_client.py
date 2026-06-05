"""Read-only HTTP client: method confinement, loopback guard, fail-closed."""

from __future__ import annotations

import pytest

from dcp_facade.http_client import ReadOnlyHttpClient, ReadOnlyHttpError


def test_get_builds_call(make_client):
    client, ft = make_client(json_body={"ok": True})
    resp = client.get("http://127.0.0.1:3004", "/api/decisions", {"limit": 20})
    assert resp.ok and resp.json == {"ok": True}
    assert ft.last["method"] == "GET"
    assert ft.last["url"] == "http://127.0.0.1:3004/api/decisions"
    assert ft.last["params"] == {"limit": 20}


def test_post_read_requires_allowlisted_path(make_client):
    client, _ = make_client()
    allowed = frozenset({"/tools/memory_search"})
    # allowed path works
    client.post_read("http://127.0.0.1:3020", "/tools/memory_search", {"q": "x"}, allowed)
    # non-allowlisted path rejected
    with pytest.raises(ReadOnlyHttpError):
        client.post_read("http://127.0.0.1:3020", "/tools/memory_correct", {}, allowed)


def test_non_loopback_base_url_rejected(make_client):
    client, _ = make_client()
    for bad in ("http://evil.example.com", "http://10.0.0.5:3004", "http://0.0.0.0:3004"):
        with pytest.raises(ReadOnlyHttpError):
            client.get(bad, "/api/decisions")


def test_non_http_scheme_rejected(make_client):
    client, _ = make_client()
    with pytest.raises(ReadOnlyHttpError):
        client.get("file:///etc/passwd", "/x")


def test_localhost_and_127_allowed(make_client):
    client, _ = make_client()
    client.get("http://localhost:3004", "/api/progress")
    client.get("http://127.0.0.1:3004", "/api/progress")
    client.get("http://127.5.5.5:3004", "/api/progress")  # 127.0.0.0/8
    client.get("http://[::1]:3004", "/api/progress")       # IPv6 loopback
    client.get("http://localhost.:3004", "/api/progress")  # trailing dot normalized
    # IPv4-mapped IPv6 loopback genuinely maps to 127.0.0.1 — a valid loopback form.
    client.get("http://[::ffff:127.0.0.1]:3004", "/api/progress")


def test_unspecified_and_routed_addresses_rejected(make_client):
    client, _ = make_client()
    for bad in ("http://0.0.0.0:3004", "http://[::]:3004", "http://[::ffff:8.8.8.8]:3004"):
        with pytest.raises(ReadOnlyHttpError):
            client.get(bad, "/x")


def test_path_with_query_or_fragment_rejected(make_client):
    client, _ = make_client()
    for bad_path in ("/api/search/x?type=all", "/api/decisions#frag"):
        with pytest.raises(ReadOnlyHttpError):
            client.get("http://127.0.0.1:3004", bad_path)


def test_relative_path_rejected(make_client):
    client, _ = make_client()
    with pytest.raises(ReadOnlyHttpError):
        client.get("http://127.0.0.1:3004", "api/decisions")  # no leading slash


def test_backend_exception_fails_closed(make_client):
    client, _ = make_client(raise_exc=TimeoutError("boom"))
    with pytest.raises(ReadOnlyHttpError):
        client.get("http://127.0.0.1:3004", "/api/decisions")


def test_no_mutating_methods_exist():
    # Structural guarantee: the public surface is GET + post_read only.
    public = {n for n in dir(ReadOnlyHttpClient) if not n.startswith("_")}
    assert public == {"get", "post_read"}
    for verb in ("put", "patch", "delete", "request"):
        assert not hasattr(ReadOnlyHttpClient, verb)
