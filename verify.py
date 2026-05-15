"""Verify advisors by querying arXiv for author matches.

NOTE: This module is temporarily disabled in main.py (as of 2026-05-11)
because the arXiv API endpoint (export.arxiv.org/api/query) experiences
persistent read timeouts from the current network environment. The
timeout-safe implementation remains in place and can be re-enabled once
connectivity is restored.
"""
import logging
from typing import Any

import arxiv
import feedparser
import requests
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

ARXIV_API_URL = "http://export.arxiv.org/api/query"

logger = logging.getLogger(__name__)


def _normalize(s: str) -> str:
    """Lowercase and remove spaces, hyphens, periods."""
    s = s.lower()
    for ch in (" ", "-", "."):
        s = s.replace(ch, "")
    return s


def fuzzy_match(name_en: str, author_str: str) -> bool:
    """Check if name_en fuzzy-matches author_str after normalization.

    Normalization lowercases and removes spaces, hyphens, periods.
    A match occurs when:
      - The fully-normalized name is a substring of the fully-normalized
        author string (or vice-versa), OR
      - Every space-separated token of the name appears as a substring in
        the fully-normalized author string.
    """
    n1 = _normalize(name_en)
    n2 = _normalize(author_str)
    if not n1 or not n2:
        return False

    if n1 in n2 or n2 in n1:
        return True

    # Token-level fallback: required for spec example "defu lian" -> "liandefu"
    tokens = [t for t in name_en.lower().split(" ") if t]
    return all(_normalize(t) in n2 for t in tokens)


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((TimeoutError, requests.exceptions.RequestException)),
    reraise=True,
)
def _search_arxiv(query: str) -> list[arxiv.Result]:
    """Query arxiv API directly with timeout."""
    params = {
        "search_query": query,
        "max_results": 3,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    resp = requests.get(ARXIV_API_URL, params=params, timeout=10)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)

    results = []
    for entry in feed.entries:
        try:
            results.append(arxiv.Result._from_feed_entry(entry))
        except arxiv.Result.MissingFieldError:
            continue
    return results


def verify_advisors(advisors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Verify each advisor by checking arxiv results for author matches.

    Modifies each advisor dict in-place:
      - Sets advisor["verified"] = True/False
      - Sets advisor["error"] = str(e) on failure after retries

    Already-verified advisors (advisor.get("verified") is not None) are skipped.
    """
    for advisor in advisors:
        if advisor.get("verified") is not None:
            logger.info("Skipping already-verified advisor: %s", advisor.get("name_en"))
            continue

        name_en = advisor.get("name_en", "")
        bridge_paper = advisor.get("bridge_paper", {}) or {}
        query = bridge_paper.get("arxiv_query", "")

        if not name_en or not query:
            advisor["verified"] = False
            advisor["error"] = "Missing name_en or arxiv_query"
            logger.warning("Missing fields for advisor: %s", name_en or "<unknown>")
            continue

        try:
            results = _search_arxiv(query)
        except (RetryError, requests.exceptions.RequestException) as e:
            advisor["verified"] = False
            advisor["error"] = str(e)
            logger.exception("arxiv search failed for %s after retries", name_en)
            continue

        verified = any(
            fuzzy_match(name_en, str(author))
            for result in results
            for author in result.authors
        )
        advisor["verified"] = verified
        logger.info("Advisor %s verified=%s (results=%d)", name_en, verified, len(results))

    return advisors
