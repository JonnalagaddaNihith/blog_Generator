from app.services.backlinks import (
    rank_link_sources,
    format_link_sources,
    count_backlinks,
    ensure_source_links,
)


def _result(url, title="Title"):
    return {"title": title, "url": url, "snippet": "", "engine": "", "category": ""}


def test_rank_prefers_authoritative_domains():
    results = [
        _result("https://example-blog.com/a", "Blog"),
        _result("https://www.fda.gov/drugs/x", "FDA"),
        _result("https://news-site.org/story", "News"),
    ]
    ranked = rank_link_sources(results)
    assert ranked[0]["domain"] == "fda.gov"
    assert ranked[0]["score"] > ranked[1]["score"]


def test_rank_dedupes_by_domain():
    results = [
        _result("https://example.com/a"),
        _result("https://www.example.com/b"),
        _result("https://other.com/c"),
    ]
    ranked = rank_link_sources(results)
    domains = [s["domain"] for s in ranked]
    assert domains.count("example.com") == 1
    assert "other.com" in domains


def test_rank_blocks_social_domains():
    results = [_result("https://www.facebook.com/page"), _result("https://site.com/a")]
    ranked = rank_link_sources(results)
    assert all(s["domain"] != "facebook.com" for s in ranked)


def test_rank_skips_invalid_urls():
    results = [{"title": "No URL"}, _result("ftp://bad.com/x"), _result("https://ok.com/a")]
    ranked = rank_link_sources(results)
    assert [s["domain"] for s in ranked] == ["ok.com"]


def test_count_backlinks_counts_unique_domains():
    content = (
        "See [one](https://a.com/x) and [two](https://a.com/y) "
        "plus [three](https://b.org/z)."
    )
    assert count_backlinks(content) == 2


def test_ensure_source_links_noop_when_enough_links():
    content = "[a](https://a.com/1) [b](https://b.com/2) [c](https://c.com/3)"
    sources = [_result("https://d.com/4")]
    out, count = ensure_source_links(content, sources)
    assert out == content
    assert count == 3


def test_ensure_source_links_appends_sources_section():
    content = "No links here."
    sources = [
        _result("https://www.fda.gov/x", "FDA Guide"),
        _result("https://who.int/y", "WHO"),
        _result("https://example.org/z", "Example"),
    ]
    out, count = ensure_source_links(content, sources)
    assert count == 3
    assert "## Sources" in out
    assert "https://www.fda.gov/x" in out
    assert "https://who.int/y" in out
    assert "https://example.org/z" in out


def test_ensure_source_links_top_up_partial_links():
    content = "One link [here](https://a.com/1)."
    sources = [
        _result("https://b.com/2", "B"),
        _result("https://c.com/3", "C"),
    ]
    out, count = ensure_source_links(content, sources)
    assert count == 3
    # Both missing sources appended to reach the minimum of 3
    assert "https://b.com/2" in out
    assert "https://c.com/3" in out


def test_format_link_sources():
    sources = [{"title": "T", "url": "https://x.com", "domain": "x.com", "score": 0, "position": 0}]
    assert format_link_sources(sources) == "- T (https://x.com)"
    assert format_link_sources([]) == ""


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
