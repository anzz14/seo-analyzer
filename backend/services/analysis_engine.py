from __future__ import annotations

import re
import string
from collections import Counter

STOPWORDS = {
	"the",
	"a",
	"an",
	"is",
	"it",
	"in",
	"on",
	"at",
	"to",
	"for",
	"of",
	"and",
	"or",
	"but",
	"be",
	"was",
	"with",
	"as",
	"by",
	"from",
	"that",
	"this",
	"are",
	"were",
	"been",
	"has",
	"have",
	"had",
	"not",
	"if",
	"do",
	"did",
	"so",
	"up",
	"out",
	"about",
	"what",
	"which",
	"who",
	"will",
	"would",
	"there",
	"their",
	"then",
	"than",
	"into",
	"he",
	"she",
	"we",
	"they",
	"his",
	"her",
	"its",
	"our",
	"your",
	"my",
	"i",
	"you",
}


def compute_word_count(text: str) -> int:
	tokens = [token for token in text.split() if token]
	return len(tokens)


def _normalize_words(text: str) -> list[str]:
	translator = str.maketrans("", "", string.punctuation)
	cleaned = text.lower().translate(translator)
	return [word for word in cleaned.split() if word]


def _count_syllables(word: str) -> int:
	vowel_groups = re.findall(r"[aeiou]+", word.lower())
	return max(1, len(vowel_groups)) if word else 0


def compute_readability_score(text: str) -> float:
	words = [word for word in _normalize_words(text) if word]
	if not words:
		return 0.0

	sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
	sentence_count = max(1, len(sentences))
	word_count = len(words)
	syllable_count = sum(_count_syllables(word) for word in words)

	score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)
	return max(0.0, min(100.0, score))


def compute_primary_keywords(text: str, top_n: int = 10) -> list[dict]:
	if top_n <= 0:
		return []

	words = _normalize_words(text)
	if not words:
		return []

	filtered_words = [word for word in words if word not in STOPWORDS]
	if not filtered_words:
		return []

	total_word_count = len(words)
	frequencies = Counter(filtered_words)
	top_keywords = sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))[:top_n]

	return [
		{
			"keyword": keyword,
			"count": count,
			"density": (count / total_word_count) * 100,
		}
		for keyword, count in top_keywords
	]


def compute_summary(text: str, num_sentences: int = 3) -> str:
	if not text.strip() or num_sentences <= 0:
		return ""

	sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text.strip()) if sentence.strip()]
	if not sentences:
		return ""
	if len(sentences) <= num_sentences:
		return ". ".join(sentence.rstrip(".!?") for sentence in sentences)

	keyword_data = compute_primary_keywords(text)
	keyword_weights = {item["keyword"]: item["count"] for item in keyword_data}

	scored_sentences: list[tuple[int, int, str]] = []
	for index, sentence in enumerate(sentences):
		words = _normalize_words(sentence)
		score = sum(keyword_weights.get(word, 0) for word in words)
		scored_sentences.append((score, index, sentence))

	top_scored = sorted(scored_sentences, key=lambda item: (-item[0], item[1]))[:num_sentences]
	ordered_sentences = [item[2] for item in sorted(top_scored, key=lambda item: item[1])]
	return ". ".join(sentence.rstrip(".!?") for sentence in ordered_sentences)


def compute_all(text: str) -> dict:
	return {
		"word_count": compute_word_count(text),
		"readability_score": compute_readability_score(text),
		"primary_keywords": compute_primary_keywords(text),
		"auto_summary": compute_summary(text),
	}
