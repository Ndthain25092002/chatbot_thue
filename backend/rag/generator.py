from __future__ import annotations

import re
from typing import Any, Dict, List

import requests

from config import settings


class Generator:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.generator_model
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.timeout = settings.generator_timeout_sec
        self.temperature = settings.generator_temperature
        self.max_contexts = settings.generator_max_contexts

    def _normalize_sources(self, contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for idx, ctx in enumerate(contexts[: self.max_contexts], start=1):
            normalized.append(
                {
                    "id": f"S{idx}",
                    "chunk_id": str(ctx.get("chunk_id") or ""),
                    "source": str(ctx.get("source") or ""),
                    "title": str(ctx.get("title") or ""),
                    "content": str(ctx.get("content") or "").strip(),
                    "score": float(ctx.get("score") or 0.0),
                }
            )
        return normalized

    def _build_context_block(self, sources: List[Dict[str, Any]]) -> str:
        lines: List[str] = []
        for src in sources:
            if not src["content"]:
                continue
            label = src["id"]
            title = src["title"] or "(khong co tieu de)"
            source = src["source"] or "(khong ro nguon)"
            lines.append(f"[{label}] title={title}; source={source}")
            lines.append(src["content"])
            lines.append("")
        return "\n".join(lines).strip()

    def _build_messages(self, question: str, context_block: str) -> List[Dict[str, str]]:
        system_prompt = (
            "Ban la tro ly phap ly cho linh vuc thue/phi/le phi Viet Nam. "
            "Chi duoc tra loi dua tren ngu canh duoc cung cap. "
            "Tra loi truc tiep vao cau hoi, khong dua huong dan chung chung, khong viet checklist. "
            "Neu ngu canh khong du de ket luan, phai noi ro phan thieu va yeu cau bo sung. "
            "Bat buoc trich dan ma nguon dang [Sx] o moi nhan dinh quan trong."
        )
        user_prompt = (
            f"Cau hoi:\n{question}\n\n"
            f"Ngu canh truy xuat:\n{context_block}\n\n"
            "Yeu cau dinh dang:\n"
            "1) Cau dau tien: tra loi truc tiep cho cau hoi.\n"
            "2) 2-4 y chinh toi da, ngan gon, dung thuat ngu phap ly.\n"
            "3) Moi y co trich dan [Sx].\n"
            "4) Tuyet doi khong viet huong dan kieu 'ban can', 'de xu ly', 'cac buoc thuc hien'."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _split_sentences(self, text: str) -> List[str]:
        parts = re.split(r"(?<=[\.!?])\s+", text.strip())
        return [p.strip() for p in parts if p.strip()]

    def _tokenize_vi(self, text: str) -> set[str]:
        tokens = re.findall(r"[0-9A-Za-zÀ-ỹ]{2,}", (text or "").lower())
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
        return {t for t in tokens if t not in stop_words}

    def _is_generic_answer(self, answer: str) -> bool:
        lowered = (answer or "").strip().lower()
        if not lowered:
            return True

        generic_markers = [
            "de xu ly van de",
            "ban can",
            "nguyen tac",
            "tim hieu ro",
            "dinh ro muc tieu",
            "kiem tra lai thong tin",
            "dam bao ngu phap",
            "cac buoc",
        ]
        if any(marker in lowered for marker in generic_markers):
            return True

        numbered_steps = re.findall(r"(?:^|\n)\s*\d+\.", answer)
        if len(numbered_steps) >= 4:
            return True

        return False

    def _grounded_extractive_answer(self, question: str, sources: List[Dict[str, Any]]) -> str:
        if not sources:
            return "Khong tim thay ngu canh phu hop de tra loi cau hoi nay."

        q_tokens = self._tokenize_vi(question)
        q_norm = (question or "").lower()
        pit_query = (
            "thu nhap ca nhan" in q_norm
            or "tncn" in q_norm
            or "thue thu nhap ca nhan" in q_norm
        )
        best_sentence = ""
        best_source_id = "S1"
        best_score = -1.0

        for src in sources:
            content = str(src.get("content") or "").strip()
            if not content:
                continue
            for sent in self._split_sentences(content):
                s_tokens = self._tokenize_vi(sent)
                overlap = len(q_tokens.intersection(s_tokens))
                score = overlap + (0.5 if re.search(r"\d", sent) else 0.0)

                sent_norm = sent.lower()
                if pit_query:
                    if (
                        "thu nhap ca nhan" in sent_norm
                        or "tncn" in sent_norm
                        or "thue thu nhap ca nhan" in sent_norm
                    ):
                        score += 2.0
                    if (
                        "thu nhap doanh nghiep" in sent_norm
                        or "tndn" in sent_norm
                        or "doanh nghiep" in sent_norm
                    ):
                        score -= 1.0

                if score > best_score:
                    best_score = score
                    best_sentence = sent
                    best_source_id = str(src.get("id") or "S1")

        if not best_sentence:
            fallback = str(sources[0].get("content") or "").strip()
            best_sentence = fallback[:450] + ("..." if len(fallback) > 450 else "")
            best_source_id = str(sources[0].get("id") or "S1")

        return (
            f"Theo ngu canh truy xuat, thong tin lien quan nhat la: {best_sentence} [{best_source_id}]\n"
            "Neu ban can ket luan chinh xac theo truong hop cu the, hay bo sung nam tinh thue, "
            "nguon thu nhap va thong tin giam tru gia canh de doi chieu dieu khoan ap dung."
        )

    def _compute_confidence(self, sources: List[Dict[str, Any]], answer: str) -> float:
        if not sources:
            return 0.0
        avg_score = sum(src["score"] for src in sources) / max(len(sources), 1)
        citation_bonus = 0.15 if "[S" in answer else 0.0
        length_bonus = min(0.2, 0.04 * len(sources))
        confidence = 0.35 + (0.35 * max(0.0, min(1.0, avg_score))) + citation_bonus + length_bonus
        return round(min(0.95, confidence), 3)

    def _fallback_answer(self, question: str, sources: List[Dict[str, Any]], error: str) -> str:
        if not sources:
            return (
                "He thong chua co ngu canh phu hop de tra loi cau hoi nay. "
                "Vui long mo rong cau hoi hoac cap nhat du lieu phap ly."
            )
        top = sources[0]
        snippet = (top.get("content") or "").strip()
        if len(snippet) > 500:
            snippet = snippet[:500].rstrip() + "..."
        return (
            "Khong goi duoc model sinh cau tra loi (Ollama). "
            f"Tam thoi tra ve tom tat ngu canh lien quan nhat [S1]:\n{snippet}\n\n"
            f"(Chi tiet loi ky thuat: {error})"
        )

    def generate_answer(self, question: str, contexts: list[dict]) -> dict:
        """Generate an answer using Ollama chat API and retrieved contexts."""
        sources = self._normalize_sources(contexts)
        context_block = self._build_context_block(sources)

        if not context_block:
            return {
                "answer": (
                    "Khong tim thay ngu canh phu hop trong bo du lieu de tra loi cau hoi nay."
                ),
                "sources": sources,
                "confidence": 0.0,
                "model": self.model_name,
            }

        messages = self._build_messages(question, context_block)
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            message = data.get("message") if isinstance(data, dict) else {}
            answer = ""
            if isinstance(message, dict):
                answer = str(message.get("content") or "").strip()
            if not answer and isinstance(data, dict):
                answer = str(data.get("response") or "").strip()
            if not answer:
                raise ValueError("Empty answer from Ollama response")

            if self._is_generic_answer(answer):
                answer = self._grounded_extractive_answer(question, sources)
        except Exception as exc:
            answer = self._fallback_answer(question, sources, str(exc))

        return {
            "answer": answer,
            "sources": sources,
            "confidence": self._compute_confidence(sources, answer),
            "model": self.model_name,
        }
