from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, Sequence


class Summarizer:
	"""Lightweight extractive summarizer for short news-like texts."""

	_sentence_splitter = re.compile(r"(?<=[.!?])\s+")
	_token_pattern = re.compile(r"[A-Za-zÀ-ÿ0-9']+")

	# Compact stopword list (EN + FR) to keep keyword scoring useful.
	_stopwords = {
		"a",
		"an",
		"and",
		"are",
		"as",
		"at",
		"au",
		"aux",
		"avec",
		"ce",
		"ces",
		"dans",
		"de",
		"des",
		"du",
		"en",
		"et",
		"for",
		"from",
		"il",
		"in",
		"is",
		"la",
		"le",
		"les",
		"of",
		"on",
		"or",
		"pour",
		"sur",
		"that",
		"the",
		"to",
		"un",
		"une",
		"with",
	}

	def summarize_text(self, text: str, max_sentences: int = 2) -> str:
		"""Return an extractive summary of a text.

		The algorithm scores sentences by keyword frequency and returns the
		highest scoring ones in original order.
		"""
		text = (text or "").strip()
		if not text:
			return "No content available to summarize."

		sentences = self._split_sentences(text)
		if len(sentences) <= max_sentences:
			return " ".join(sentences)

		frequencies = self._keyword_frequencies(sentences)
		if not frequencies:
			return " ".join(sentences[:max_sentences])

		scored = []
		for index, sentence in enumerate(sentences):
			score = self._sentence_score(sentence, frequencies)
			scored.append((score, index, sentence))

		best_indexes = {idx for _, idx, _ in sorted(scored, reverse=True)[:max_sentences]}
		selected = [sentence for idx, sentence in enumerate(sentences) if idx in best_indexes]
		return " ".join(selected)

	def summarize_articles(
		self,
		articles: Sequence[dict],
		*,
		max_articles: int = 3,
		max_sentences_per_article: int = 1,
	) -> str:
		"""Create a concise cross-article summary from article dictionaries.

		Expected article keys: ``title`` and optional ``content``.
		"""
		if not articles:
			return "No relevant articles were found for this topic."

		slices = []
		for article in list(articles)[:max_articles]:
			title = str(article.get("title") or "Untitled").strip()
			content = str(article.get("content") or article.get("summary") or "").strip()
			base_text = content if content else title
			condensed = self.summarize_text(base_text, max_sentences=max_sentences_per_article)
			slices.append(f"- {title}: {condensed}")

		return "\n".join(slices)

	def _split_sentences(self, text: str) -> list[str]:
		raw = self._sentence_splitter.split(text)
		cleaned = [item.strip() for item in raw if item and item.strip()]
		return cleaned if cleaned else [text]

	def _keyword_frequencies(self, sentences: Iterable[str]) -> Counter:
		tokens = []
		for sentence in sentences:
			for token in self._token_pattern.findall(sentence.lower()):
				if token not in self._stopwords and len(token) > 2:
					tokens.append(token)
		return Counter(tokens)

	def _sentence_score(self, sentence: str, frequencies: Counter) -> float:
		tokens = self._token_pattern.findall(sentence.lower())
		if not tokens:
			return 0.0
		return sum(float(frequencies.get(token, 0)) for token in tokens) / max(len(tokens), 1)


def summarize_text(text: str, max_sentences: int = 2) -> str:
	"""Convenience function for summarizing raw text."""
	return Summarizer().summarize_text(text, max_sentences=max_sentences)


def summarize_articles(
	articles: Sequence[dict],
	*,
	max_articles: int = 3,
	max_sentences_per_article: int = 1,
) -> str:
	"""Convenience function for summarizing article dictionaries."""
	return Summarizer().summarize_articles(
		articles,
		max_articles=max_articles,
		max_sentences_per_article=max_sentences_per_article,
	)
