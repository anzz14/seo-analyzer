from __future__ import annotations

import re
import string
from collections import Counter

STOPWORDS = {
    "the", "a", "an", "is", "it", "in", "on", "at", "to", "for", "of",
    "and", "or", "but", "be", "was", "with", "as", "by", "from", "that",
    "this", "are", "were", "been", "has", "have", "had", "not", "if", "do",
    "did", "so", "up", "out", "about", "what", "which", "who", "will",
    "would", "there", "their", "then", "than", "into", "he", "she", "we",
    "they", "his", "her", "its", "our", "your", "my", "i", "you", "me",
    "him", "us", "them", "also", "just", "more", "can", "all", "one",
    "two", "any", "when", "where", "how", "get", "got", "let", "may",
    "might", "much", "such", "very", "even", "well", "back", "still",
    "after", "before", "over", "while", "been", "being", "am",
}

# Words that end silent 'e' — used to adjust syllable count
_SILENT_E = re.compile(r"[^aeiou]e$")
# Consecutive vowels that count as one syllable
_VOWEL_RUNS = re.compile(r"[aeiouy]+")


def compute_word_count(text: str) -> int:
    return len(text.split())


def _normalize_words(text: str) -> list[str]:
    translator = str.maketrans("", "", string.punctuation)
    return [w for w in text.lower().translate(translator).split() if w]


def _count_syllables(word: str) -> int:
    """More accurate syllable counter using vowel-run heuristics."""
    word = word.lower().rstrip(".,!?;:")
    if not word:
        return 0
    count = len(_VOWEL_RUNS.findall(word))
    # Silent trailing 'e' (e.g. "make", "have") — don't count it
    if len(word) > 2 and _SILENT_E.search(word):
        count -= 1
    # 'le' ending counts as a syllable (e.g. "ta-ble", "sim-ple")
    if word.endswith("le") and len(word) > 2 and word[-3] not in "aeiou":
        count += 1
    return max(1, count)


def compute_readability_score(text: str) -> float:
    """Flesch Reading Ease score (0–100, higher = easier)."""
    words = _normalize_words(text)
    if not words:
        return 0.0
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    # Fallback for punctuation-light text: treat commas/semicolons as sentence boundaries.
    if len(sentences) <= 1:
        sentences = [s.strip() for s in re.split(r"[.!?,;]+", text) if s.strip()]
    sentence_count = max(1, len(sentences))
    word_count = len(words)
    syllable_count = sum(_count_syllables(w) for w in words)
    score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)
    return round(max(0.0, min(100.0, score)), 2)


def _extract_ngrams(words: list[str], n: int) -> list[str]:
    return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]


def compute_primary_keywords(text: str, top_n: int = 10) -> list[dict]:
    """
    Returns top unigrams + bigrams ranked by frequency.
    Density is calculated against total non-stopword words for more
    meaningful SEO percentages.
    """
    if top_n <= 0:
        return []

    all_words = _normalize_words(text)
    if not all_words:
        return []

    content_words = [w for w in all_words if w not in STOPWORDS and len(w) > 2]
    if not content_words:
        return []

    total = len(content_words)

    # Unigrams
    unigram_counts = Counter(content_words)

    # Bigrams (only from content words in sequence)
    bigrams = _extract_ngrams(content_words, 2)
    bigram_counts = Counter(bigrams)

    # Merge: add frequent bigrams without suppressing valid unigrams.
    candidates: dict[str, int] = dict(unigram_counts)
    for bigram, count in bigram_counts.items():
        if count >= 2:
            candidates[bigram] = count

    top = sorted(candidates.items(), key=lambda x: (-x[1], x[0]))[:top_n]

    return [
        {
            "keyword": kw,
            "count": count,
            "density": round((count / total) * 100, 2),
        }
        for kw, count in top
    ]


def compute_summary(text: str, num_sentences: int = 3) -> str:
    """
    Extractive summary — picks highest-scoring sentences by keyword weight.
    Filters out very short sentences (< 5 words) to avoid fragment summaries.
    """
    if not text.strip() or num_sentences <= 0:
        return ""

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    # Filter fragments
    sentences = [s for s in sentences if len(s.split()) >= 5]

    if not sentences:
        return ""
    if len(sentences) <= num_sentences:
        return " ".join(sentences)

    keyword_data = compute_primary_keywords(text)
    keyword_weights = {item["keyword"]: item["count"] for item in keyword_data}

    scored: list[tuple[float, int, str]] = []
    for idx, sentence in enumerate(sentences):
        words = _normalize_words(sentence)
        raw_score = sum(keyword_weights.get(w, 0) for w in words)
        # Normalize by sentence length to avoid always picking the longest sentence
        length_penalty = len(words) ** 0.5
        normalized = raw_score / length_penalty if length_penalty else 0
        scored.append((normalized, idx, sentence))

    top = sorted(scored, key=lambda x: (-x[0], x[1]))[:num_sentences]
    ordered = [s for _, _, s in sorted(top, key=lambda x: x[1])]
    return " ".join(ordered)


def compute_reading_time(word_count: int, wpm: int = 200) -> int:
    """Returns estimated reading time in seconds."""
    return max(1, round((word_count / wpm) * 60))


def compute_sentence_stats(text: str) -> dict:
    """Avg sentence length and sentence count — useful SEO signals."""
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        return {"sentence_count": 0, "avg_sentence_length": 0.0}
    lengths = [len(s.split()) for s in sentences]
    return {
        "sentence_count": len(sentences),
        "avg_sentence_length": round(sum(lengths) / len(lengths), 1),
    }


def compute_all(text: str) -> dict:
    word_count = compute_word_count(text)
    stats = compute_sentence_stats(text)
    return {
        "word_count": word_count,
        "readability_score": compute_readability_score(text),
        "primary_keywords": compute_primary_keywords(text),
        "auto_summary": compute_summary(text),
        "reading_time_seconds": compute_reading_time(word_count),
        "sentence_count": stats["sentence_count"],
        "avg_sentence_length": stats["avg_sentence_length"],
    }