class Reranker:
    """Optional reranker stage for improving retrieval quality."""

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join((text or "").lower().split())

    @staticmethod
    def _tokens(text: str) -> set[str]:
        raw = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in (text or "").lower())
        stop_words = {
            "la",
            "va",
            "cua",
            "cho",
            "trong",
            "duoc",
            "nhung",
            "nhu",
            "voi",
            "toi",
            "ban",
            "mot",
            "cac",
            "ve",
            "tu",
            "khi",
            "nao",
        }
        return {tok for tok in raw.split() if len(tok) >= 2 and tok not in stop_words}

    def _score_candidate(self, query: str, candidate: dict) -> float:
        query_norm = self._normalize(query)
        title = self._normalize(str(candidate.get("title") or ""))
        content = self._normalize(str(candidate.get("content") or ""))

        base = float(candidate.get("score") or 0.0)

        q_tokens = self._tokens(query_norm)
        t_tokens = self._tokens(title)
        c_tokens = self._tokens(content)

        overlap_title = len(q_tokens.intersection(t_tokens))
        overlap_content = len(q_tokens.intersection(c_tokens))

        lexical = (0.10 * overlap_title) + (0.04 * overlap_content)

        pit_query = (
            "thu nhap ca nhan" in query_norm
            or "tncn" in query_norm
            or "thue thu nhap" in query_norm
        )
        if pit_query:
            pit_hit = any(
                key in f"{title} {content}"
                for key in ["thu nhap ca nhan", "tncn", "thue thu nhap ca nhan"]
            )
            if pit_hit:
                lexical += 0.30
            else:
                lexical -= 0.10

        return base + lexical

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        if not candidates:
            return []
        scored = sorted(candidates, key=lambda c: self._score_candidate(query, c), reverse=True)
        return scored[:top_k]
