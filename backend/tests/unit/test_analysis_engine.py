from __future__ import annotations

from services.analysis_engine import (
    compute_all,
    compute_primary_keywords,
    compute_readability_score,
    compute_word_count,
)


def test_compute_word_count_basic() -> None:
    assert compute_word_count("hello world") == 2


def test_compute_word_count_empty() -> None:
    assert compute_word_count("") == 0


def test_compute_primary_keywords_excludes_stopwords() -> None:
    keywords = compute_primary_keywords("the and is seo content strategy")
    keyword_names = {item["keyword"] for item in keywords}

    assert "the" not in keyword_names
    assert "and" not in keyword_names
    assert "is" not in keyword_names
    assert "seo" in keyword_names


def test_compute_readability_score_in_range() -> None:
    score = compute_readability_score("This is a short sentence. This is another simple sentence.")

    assert isinstance(score, float)
    assert 0 <= score <= 100


def test_compute_all_returns_expected_keys() -> None:
    result = compute_all("SEO tools help improve readability and keyword relevance.")

    assert set(result.keys()) == {
        "word_count",
        "readability_score",
        "primary_keywords",
        "auto_summary",
    }
