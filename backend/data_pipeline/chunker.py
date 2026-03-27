class Chunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> list[str]:
        if not text:
            return []

        chunks: list[str] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunks.append(text[start:end])
            if end >= text_length:
                break
            start = max(0, end - self.chunk_overlap)
        return chunks

    def chunk_legal_document(self, document: dict) -> list[dict]:
        """Chunk a processed legal document to structured schema.

        Output schema:
        {
          "chunk_id": str,
          "law_name": str,
          "article": str,
          "clause": str,
          "title": str,
          "content": str,
          "source": str,
          "tokens_estimate": int
        }
        """
        content = document.get("content", "")
        if not isinstance(content, str) or not content.strip():
            return []

        law_name = document.get("law_name", "Văn bản pháp luật")
        article = document.get("article", "Điều chưa xác định")
        clause = document.get("clause", "Khoản chưa xác định")
        title = document.get("title", "Tiêu đề chưa xác định")
        source = document.get("source", "unknown")

        chunk_texts = self.chunk_text(content)
        if not chunk_texts:
            return []

        law_code = self._build_law_code(law_name)
        article_num = self._extract_numeric_token(article, fallback="X")
        clause_num = self._extract_numeric_token(clause, fallback="X")
        base_chunk_id = f"{law_code}_Dieu{article_num}_Khoan{clause_num}"

        chunks: list[dict] = []
        for idx, chunk_content in enumerate(chunk_texts, start=1):
            chunk_id = base_chunk_id if len(chunk_texts) == 1 else f"{base_chunk_id}_P{idx}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "law_name": law_name,
                    "article": article,
                    "clause": clause,
                    "title": title,
                    "content": chunk_content,
                    "source": source,
                    "tokens_estimate": self._estimate_tokens(chunk_content),
                }
            )

        return chunks

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        words = len(text.split())
        return max(1, int(words * 1.3))

    @staticmethod
    def _extract_numeric_token(text: str, fallback: str = "X") -> str:
        import re

        if not isinstance(text, str):
            return fallback
        match = re.search(r"\d+[A-Za-z]?", text)
        return match.group(0) if match else fallback

    @staticmethod
    def _build_law_code(law_name: str) -> str:
        import re

        if not isinstance(law_name, str) or not law_name.strip():
            return "VBPL"

        normalized = law_name.strip()
        prefix_letters = re.sub(r"[^A-Za-zÀ-ỹ\s]", "", normalized)
        prefix_letters = "".join(word[:1] for word in prefix_letters.split()[:4]).upper()
        year_match = re.search(r"(19\d{2}|20\d{2})", normalized)
        year = year_match.group(1) if year_match else ""

        if not prefix_letters:
            prefix_letters = "VBPL"
        return f"{prefix_letters}{year}"
