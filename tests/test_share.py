import json
import urllib.error
import urllib.request

import pytest

from ps5_translator.share import ShareServer


@pytest.fixture
def server():
    s = ShareServer(code="secret", port=0, host="127.0.0.1")
    s.start()
    yield s
    s.stop()


def get(server, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{server.port}{path}", timeout=5) as r:
        return r.read().decode("utf-8")


def test_page_is_served_only_with_the_code(server):
    assert "<title>Altyazı</title>" in get(server, "/secret/")
    for path in ["/", "/wrong/", "/secret", "/secret/other", "/secret/../x"]:
        with pytest.raises(urllib.error.HTTPError) as err:
            get(server, path)
        assert err.value.code == 404


def test_lines_are_returned_incrementally(server):
    server.add_line("Anahtar nerede?", "Where is the key?")
    server.add_line("Gidelim.", "Let's go.")
    first = json.loads(get(server, "/secret/lines?after=0"))
    assert first["total"] == 2
    assert [l["translated"] for l in first["lines"]] == ["Anahtar nerede?", "Gidelim."]
    assert first["lines"][0]["source"] == "Where is the key?"
    later = json.loads(get(server, "/secret/lines?after=1"))
    assert [l["translated"] for l in later["lines"]] == ["Gidelim."]
    assert json.loads(get(server, "/secret/lines?after=2"))["lines"] == []


def test_bad_or_large_index_is_safe(server):
    server.add_line("a", "b")
    assert json.loads(get(server, "/secret/lines?after=abc"))["total"] == 1
    assert json.loads(get(server, "/secret/lines?after=999"))["lines"] == []
    assert len(json.loads(get(server, "/secret/lines?after=-5"))["lines"]) == 1


def test_only_subtitles_are_exposed(server, monkeypatch):
    monkeypatch.setenv("DEEPL_API_KEY", "top-secret-key:fx")
    server.add_line("Merhaba", "Hello")
    everything = get(server, "/secret/") + get(server, "/secret/lines?after=0")
    assert "top-secret-key" not in everything


def test_next_port_is_used_when_busy():
    a = ShareServer(code="x", port=0, host="127.0.0.1")
    b = ShareServer(code="x", port=a.port, host="127.0.0.1")
    assert b.port != a.port
    a._httpd.server_close()
    b._httpd.server_close()


def test_waiting_request_returns_as_soon_as_a_line_arrives(server):
    import threading
    import time

    threading.Timer(0.3, lambda: server.add_line("Merhaba", "Hello")).start()
    start = time.monotonic()
    data = json.loads(get(server, "/secret/lines?after=0&wait=10"))
    assert [l["translated"] for l in data["lines"]] == ["Merhaba"]
    assert time.monotonic() - start < 3


def test_waiting_request_times_out_empty(server):
    assert json.loads(get(server, "/secret/lines?after=0&wait=0.2"))["lines"] == []
