from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, List, Optional, Tuple


class LegalDocumentChunker:
	"""Chunk Vietnamese legal documents into RAG-friendly structured chunks."""

	ARTICLE_PATTERN = re.compile(
		r"(?ims)(^\s*Điều\s+\d+[^\n]*\n?.*?)(?=^\s*Điều\s+\d+|\Z)"
	)
	CLAUSE_PATTERN = re.compile(r"(?m)(?=^\s*\d+\.\s)")
	POINT_PATTERN = re.compile(r"(?m)(?<!\w)([a-zđ])\)")

	DOC_TYPE_KEYWORDS = (
		"NGHỊ QUYẾT",
		"NGHỊ ĐỊNH",
		"THÔNG TƯ",
		"QUYẾT ĐỊNH",
		"CHỈ THỊ",
		"LUẬT",
		"PHÁP LỆNH",
		"THÔNG BÁO",
		"CÔNG VĂN",
	)

	def clean_text(self, text: str) -> str:
		"""Clean malformed spacing and remove common footer artifacts."""
		if not text:
			return ""

		cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
		cleaned = re.sub(r"[ \t]+", " ", cleaned)
		cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)

		# Remove common page markers/footer noise.
		cleaned = re.sub(r"(?im)^\s*trang\s+\d+(?:\s*/\s*\d+)?\s*$", "", cleaned)
		cleaned = re.sub(
			r"(?im)^\s*\*\s*\*\s*\*\s*$",
			"",
			cleaned,
		)

		return cleaned.strip()

	def _normalize_date(self, raw_date: str) -> str:
		"""Normalize Vietnamese date formats into YYYY-MM-DD when possible."""
		date_text = raw_date.strip()

		slash_match = re.search(
			r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
			date_text,
		)
		if slash_match:
			day, month, year = slash_match.groups()
			year_value = int(year)
			if year_value < 100:
				year_value += 2000
			try:
				return date(year_value, int(month), int(day)).isoformat()
			except ValueError:
				return date_text

		vn_match = re.search(
			r"ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})",
			date_text,
			flags=re.IGNORECASE,
		)
		if vn_match:
			day, month, year = vn_match.groups()
			try:
				return date(int(year), int(month), int(day)).isoformat()
			except ValueError:
				return date_text

		return date_text

	def _extract_header(self, text: str) -> str:
		"""Return content likely belonging to document header section."""
		marker = re.search(r"(?im)^\s*Điều\s+\d+", text)
		if marker:
			return text[: marker.start()].strip()
		return text[:2000].strip()

	def _extract_body(self, text: str) -> str:
		"""Return body beginning from first article, fallback to full text."""
		marker = re.search(r"(?im)^\s*Điều\s+\d+", text)
		if marker:
			return text[marker.start() :].strip()
		return text.strip()

	def extract_metadata(self, text: str) -> Dict[str, str]:
		"""Extract core document metadata from legal document header and body."""
		cleaned = self.clean_text(text)
		header = self._extract_header(cleaned)

		metadata: Dict[str, str] = {
			"doc_type": "",
			"doc_id": "",
			"issuer": "",
			"location": "",
			"date": "",
			"effective_date": "",
			"article": "",
			"clause": "",
			"point": "",
			"title": "",
		}

		for keyword in self.DOC_TYPE_KEYWORDS:
			if re.search(rf"\b{re.escape(keyword)}\b", header, flags=re.IGNORECASE):
				metadata["doc_type"] = keyword
				break

		doc_id_match = re.search(
			r"\b\d{1,4}\s*/\s*\d{4}\s*/\s*[A-ZĐa-zđ\-]+\b",
			header,
			flags=re.IGNORECASE,
		)
		if doc_id_match:
			metadata["doc_id"] = re.sub(r"\s+", "", doc_id_match.group(0))

		issuer_match = re.search(
			r"(?im)^\s*(HỘI\s+ĐỒNG\s+NHÂN\s+DÂN[^\n]*|"
			r"ỦY\s+BAN\s+NHÂN\s+DÂN[^\n]*|"
			r"CHÍNH\s+PHỦ[^\n]*|"
			r"BỘ\s+[^\n]*|"
			r"QUỐC\s+HỘI[^\n]*)$",
			header,
		)
		if issuer_match:
			metadata["issuer"] = re.sub(r"\s+", " ", issuer_match.group(1)).strip()

		location_date_match = re.search(
			r"(?im)^\s*([A-ZÀ-ỴĐ][^,\n]{1,100})\s*,\s*"
			r"(?:ngày\s*\d{1,2}\s*tháng\s*\d{1,2}\s*năm\s*\d{4}|"
			r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
			header,
		)
		if location_date_match:
			metadata["location"] = re.sub(
				r"\s+",
				" ",
				location_date_match.group(1),
			).strip()

		date_match = re.search(
			r"(?im)(ngày\s*\d{1,2}\s*tháng\s*\d{1,2}\s*năm\s*\d{4}|"
			r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b)",
			header,
		)
		if date_match:
			metadata["date"] = self._normalize_date(date_match.group(1))

		effective_match = re.search(
			r"(?is)có\s+hiệu\s+lực\s+(?:thi\s+hành\s+)?từ\s+ngày\s*"
			r"(\d{1,2}\s*tháng\s*\d{1,2}\s*năm\s*\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
			cleaned,
		)
		if effective_match:
			metadata["effective_date"] = self._normalize_date(effective_match.group(1))

		return metadata

	def split_articles(self, text: str) -> List[str]:
		"""Split body text into article-level blocks by 'Điều X'."""
		if not text:
			return []

		body = self._extract_body(self.clean_text(text))
		articles = [match.group(1).strip() for match in self.ARTICLE_PATTERN.finditer(body)]
		if articles:
			return articles

		# Graceful fallback for malformed documents without explicit article marker.
		return [body] if body else []

	def split_clauses(self, article_text: str) -> List[str]:
		"""Split an article into clause blocks by '\n1. ', '\n2. ', etc."""
		if not article_text:
			return []

		normalized = self.clean_text(article_text)
		clause_starts = [m.start() for m in re.finditer(r"(?m)^\s*\d+\.\s", normalized)]
		if not clause_starts:
			return [normalized]

		clauses: List[str] = []
		for idx, start in enumerate(clause_starts):
			end = clause_starts[idx + 1] if idx + 1 < len(clause_starts) else len(normalized)
			chunk = normalized[start:end].strip()
			if chunk:
				clauses.append(chunk)
		return clauses or [normalized]

	def extract_title(self, article_text: str) -> str:
		"""Extract article title from the first line, fallback to empty string."""
		if not article_text:
			return ""

		first_line = article_text.strip().split("\n", 1)[0].strip()
		title_match = re.match(r"(?is)^\s*Điều\s+\d+\s*[\.:\-]?\s*(.*)$", first_line)
		if not title_match:
			return ""

		title = re.sub(r"\s+", " ", title_match.group(1)).strip(" .:-")
		return title

	def _extract_article_number(self, article_text: str) -> str:
		"""Extract article number from an article block."""
		match = re.match(r"(?is)^\s*Điều\s+(\d+)", article_text.strip())
		return match.group(1) if match else ""

	def _extract_clause_number(self, clause_text: str) -> str:
		"""Extract leading clause number from a clause block."""
		match = re.match(r"(?m)^\s*(\d+)\.\s", clause_text)
		return match.group(1) if match else ""

	def _extract_points(self, text: str) -> str:
		"""Extract point labels (a, b, c...) found inside a chunk without splitting."""
		labels = [m.group(1) for m in self.POINT_PATTERN.finditer(text)]
		seen = set()
		ordered_unique = []
		for label in labels:
			if label not in seen:
				seen.add(label)
				ordered_unique.append(label)
		return ",".join(ordered_unique)

	def _build_chunk(
		self,
		content: str,
		base_metadata: Dict[str, str],
		article_no: str,
		clause_no: str,
		article_title: str,
	) -> Dict[str, Any]:
		"""Create a single chunk object with merged metadata."""
		metadata = dict(base_metadata)
		metadata.update(
			{
				"article": article_no,
				"clause": clause_no,
				"point": self._extract_points(content),
				"title": article_title,
			}
		)
		return {
			"content": content.strip(),
			"metadata": metadata,
		}

	def _word_count(self, text: str) -> int:
		"""Count words in Vietnamese text with unicode-aware tokenization."""
		return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))

	def _attach_article_header(self, article_text: str, clause_text: str) -> str:
		"""Ensure each clause chunk keeps article heading for semantic completeness."""
		first_line = article_text.strip().split("\n", 1)[0].strip()
		clause_trimmed = clause_text.strip()
		if clause_trimmed.startswith(first_line):
			return clause_trimmed
		return f"{first_line}\n{clause_trimmed}".strip()

	def chunk_document(self, text: str) -> List[Dict[str, Any]]:
		"""Chunk a legal document by article/clauses for RAG ingestion."""
		cleaned = self.clean_text(text)
		if not cleaned:
			return []

		base_metadata = self.extract_metadata(cleaned)
		articles = self.split_articles(cleaned)
		chunks: List[Dict[str, Any]] = []

		for article in articles:
			article_clean = self.clean_text(article)
			if not article_clean:
				continue

			article_no = self._extract_article_number(article_clean)
			article_title = self.extract_title(article_clean)
			article_words = self._word_count(article_clean)

			if article_words < 500:
				chunks.append(
					self._build_chunk(
						content=article_clean,
						base_metadata=base_metadata,
						article_no=article_no,
						clause_no="",
						article_title=article_title,
					)
				)
				continue

			clauses = self.split_clauses(article_clean)
			if len(clauses) <= 1:
				chunks.append(
					self._build_chunk(
						content=article_clean,
						base_metadata=base_metadata,
						article_no=article_no,
						clause_no="",
						article_title=article_title,
					)
				)
				continue

			for clause in clauses:
				clause_no = self._extract_clause_number(clause)
				clause_with_header = self._attach_article_header(article_clean, clause)
				chunks.append(
					self._build_chunk(
						content=clause_with_header,
						base_metadata=base_metadata,
						article_no=article_no,
						clause_no=clause_no,
						article_title=article_title,
					)
				)

		return chunks


def main() -> List[Dict[str, Any]]:
	"""Example usage for local testing and integration checks."""
	sample_text = "Điều 1. Phạm vi điều chỉnh\n1. Nội dung A...\n2. Nội dung B..."
	chunker = LegalDocumentChunker()
	return chunker.chunk_document(sample_text)


if __name__ == "__main__":
	main()
