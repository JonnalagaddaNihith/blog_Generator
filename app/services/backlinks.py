"""Rank external sources and ensure generated blog content contains SEO backlinks."""
import re
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

MIN_BACKLINKS = 3
MAX_LINK_SOURCES = 8

# TLDs that indicate official/authoritative sources.
_AUTHORITY_TLD_SCORES = {
    ".gov": 4,
    ".edu": 4,
    ".mil": 4,
    ".int": 3,
    ".org": 2,
    ".ac": 2,
}

# Well-known authoritative domains that deserve a bonus regardless of TLD.
_AUTHORITY_DOMAIN_HINTS = (
    "who.int",
    "fda.gov",
    "nih.gov",
    "cdc.gov",
    "mayoclinic.org",
    "nature.com",
    "sciencedirect.com",
    "springer.com",
    "ieee.org",
    "acm.org",
    "wikipedia.org",
)

# Social/UGC domains are poor backlink targets for SEO.
_BLOCKED_DOMAINS = (
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "pinterest.com",
    "tiktok.com",
    "reddit.com",
    "quora.com",
    "medium.com",
    "linkedin.com",
)

_EXTERNAL_LINK_RE = re.compile(r"\[[^\]]*\]\(\s*(https?://[^)\s]+)[^)]*\)")


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _is_blocked(domain: str) -> bool:
    return any(domain == b or domain.endswith("." + b) for b in _BLOCKED_DOMAINS)


def _authority_score(domain: str) -> int:
    score = 0
    for tld, points in _AUTHORITY_TLD_SCORES.items():
        if domain.endswith(tld):
            score = max(score, points)
    for hint in _AUTHORITY_DOMAIN_HINTS:
        if domain == hint or domain.endswith("." + hint):
            score += 3
    return score


def rank_link_sources(
    results: List[Dict[str, Any]],
    max_sources: int = MAX_LINK_SOURCES,
) -> List[Dict[str, Any]]:
    """Dedupe research results by domain and rank official/authoritative ones first."""
    seen = set()
    candidates = []
    for position, result in enumerate(results or []):
        url = (result.get("url") or "").strip()
        domain = _domain(url)
        if not url.startswith("http") or not domain or domain in seen:
            continue
        if _is_blocked(domain):
            continue
        seen.add(domain)
        candidates.append({
            "title": result.get("title") or domain,
            "url": url,
            "domain": domain,
            "score": _authority_score(domain),
            "position": position,
        })

    candidates.sort(key=lambda s: (-s["score"], s["position"]))
    return candidates[:max_sources]


def format_link_sources(sources: List[Dict[str, Any]]) -> str:
    """Render ranked sources as a prompt-friendly list."""
    return "\n".join(f"- {s['title']} ({s['url']})" for s in sources)


def external_link_urls(content: str) -> List[str]:
    """Return all external http(s) URLs linked in markdown content."""
    return [m.group(1) for m in _EXTERNAL_LINK_RE.finditer(content or "")]


def count_backlinks(content: str) -> int:
    """Count unique external domains linked in the content."""
    return len({_domain(u) for u in external_link_urls(content) if _domain(u)})


def _domain_of(source: Dict[str, Any]) -> str:
    return source.get("domain") or _domain(source.get("url", ""))


def ensure_source_links(
    content: str,
    sources: List[Dict[str, Any]],
    min_links: int = MIN_BACKLINKS,
) -> Tuple[str, int]:
    """Guarantee at least min_links external links.

    If the generated content links fewer than min_links unique domains,
    append a 'Sources' section with the top-ranked unused sources so SEO
    backlink coverage is never zero. Returns (content, final_link_count).
    """
    linked_urls = set(external_link_urls(content))
    linked_domains = {_domain(u) for u in linked_urls if _domain(u)}
    if len(linked_domains) >= min_links or not sources:
        return content, len(linked_domains)

    missing = [
        s for s in sources
        if s.get("url") not in linked_urls and _domain_of(s) not in linked_domains
    ]
    picks = missing[: min_links - len(linked_domains)]
    if not picks:
        return content, len(linked_domains)

    section = "\n\n## Sources\n\n" + "\n".join(
        f"- [{s.get('title') or _domain_of(s)}]({s['url']})" for s in picks
    )
    return content.rstrip() + section + "\n", len(linked_domains) + len(picks)


class BacklinksService:
    """Thin wrapper exposing the module-level helpers as a service."""

    rank_link_sources = staticmethod(rank_link_sources)
    format_link_sources = staticmethod(format_link_sources)
    count_backlinks = staticmethod(count_backlinks)
    ensure_source_links = staticmethod(ensure_source_links)


backlinks_service = BacklinksService()
