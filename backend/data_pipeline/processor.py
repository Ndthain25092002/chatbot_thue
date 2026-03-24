import re
from datetime import datetime
from typing import Optional
from utils.text_cleaner import clean_text


class Processor:
    """Process and clean Vietnamese legal documents."""
    
    def __init__(self):
        self.vietnamese_stopwords = {
            "và", "hoặc", "là", "cái", "được", "để", "từ", "trong", 
            "với", "có", "nhưng", "nếu", "như", "sau", "trước", "tại",
            "của", "vào", "ra", "lên", "xuống", "qua", "về", "từng",
            "những", "sự", "việc", "được", "cho", "bằng", "bởi"
        }

    def process(self, raw_documents: list[dict]) -> list[dict]:
        """Process raw documents into clean, normalized format."""
        processed = []
        for doc in raw_documents:
            try:
                cleaned_doc = self._process_single_document(doc)
                if cleaned_doc:
                    processed.append(cleaned_doc)
            except Exception as e:
                print(f"Warning: Error processing document from {doc.get('source')}: {e}")
        
        print(f"Processed {len(processed)} documents (from {len(raw_documents)} raw)")
        return processed

    def _process_single_document(self, raw_doc: dict) -> Optional[dict]:
        """Clean and normalize a single legal document."""
        raw_content = raw_doc.get("raw_content", "").strip()
        if not raw_content:
            return None

        # Extract and clean text
        cleaned_text = self._clean_vietnamese_text(raw_content)
        
        # Extract metadata
        metadata = self._extract_metadata(raw_doc, cleaned_text)

        law_name = self._extract_law_name(raw_doc, cleaned_text)
        article = self._extract_article(raw_doc, cleaned_text)
        clause = self._extract_clause(raw_doc, cleaned_text)
        title = self._extract_title(raw_doc, cleaned_text)
        source = self._extract_source(raw_doc)
        
        # Extract document type and jurisdiction
        doc_type = self._detect_document_type(cleaned_text)
        jurisdiction = self._detect_jurisdiction(cleaned_text)

        return {
            "source": source,
            "content": cleaned_text,
            "metadata": metadata,
            "law_name": law_name,
            "article": article,
            "clause": clause,
            "title": title,
            "document_type": doc_type,
            "jurisdiction": jurisdiction,
            "word_count": len(cleaned_text.split()),
            "processed_at": datetime.now().isoformat(),
        }

    @staticmethod
    def _clean_vietnamese_text(text: str) -> str:
        """Clean Vietnamese legal text."""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        
        # Remove URLs
        text = re.sub(r"http[s]?://\S+", "", text)
        
        # Remove email addresses
        text = re.sub(r"\S+@\S+", "", text)
        
        # Fix Vietnamese diacritics spacing
        text = re.sub(r"(\w)\s{2,}", r"\1 ", text)
        
        # Use general text cleaner
        text = clean_text(text)
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        return text

    @staticmethod
    def _extract_metadata(raw_doc: dict, content: str) -> dict:
        """Extract metadata from document."""
        metadata = raw_doc.get("metadata", {}).copy() if isinstance(raw_doc.get("metadata"), dict) else {}
        
        # Add content size
        metadata["content_length"] = len(content)
        
        # Try to extract issue/effective date from content
        date_pattern = r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})"
        dates = re.findall(date_pattern, content)
        if dates:
            metadata["found_dates"] = dates[:3]  # Top 3 dates
        
        return metadata

    @staticmethod
    def _extract_law_name(raw_doc: dict, text: str) -> str:
        metadata = raw_doc.get("metadata", {}) if isinstance(raw_doc.get("metadata"), dict) else {}
        candidates = [
            metadata.get("law_name"),
            metadata.get("document_name"),
            metadata.get("name"),
            raw_doc.get("law_name"),
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

        match = re.search(r"(Bộ luật[^\n\.;:]+|Luật[^\n\.;:]+|Nghị định[^\n\.;:]+)", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return "Văn bản pháp luật"

    @staticmethod
    def _extract_article(raw_doc: dict, text: str) -> str:
        metadata = raw_doc.get("metadata", {}) if isinstance(raw_doc.get("metadata"), dict) else {}
        candidates = [
            metadata.get("article"),
            metadata.get("dieu"),
            raw_doc.get("article"),
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

        match = re.search(r"(Điều\s+\d+[A-Za-z]?)", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return "Điều chưa xác định"

    @staticmethod
    def _extract_clause(raw_doc: dict, text: str) -> str:
        metadata = raw_doc.get("metadata", {}) if isinstance(raw_doc.get("metadata"), dict) else {}
        candidates = [
            metadata.get("clause"),
            metadata.get("khoan"),
            raw_doc.get("clause"),
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

        match = re.search(r"(Khoản\s+\d+[A-Za-z]?)", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return "Khoản chưa xác định"

    @staticmethod
    def _extract_title(raw_doc: dict, text: str) -> str:
        metadata = raw_doc.get("metadata", {}) if isinstance(raw_doc.get("metadata"), dict) else {}
        candidates = [
            metadata.get("title"),
            metadata.get("heading"),
            raw_doc.get("title"),
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

        first_sentence = re.split(r"[\n\.!?]", text)[0].strip()
        return first_sentence[:180] if first_sentence else "Tiêu đề chưa xác định"

    @staticmethod
    def _extract_source(raw_doc: dict) -> str:
        metadata = raw_doc.get("metadata", {}) if isinstance(raw_doc.get("metadata"), dict) else {}
        candidates = [
            raw_doc.get("source"),
            metadata.get("source"),
            metadata.get("url"),
            metadata.get("link"),
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return "unknown"

    @staticmethod
    def _detect_document_type(text: str) -> str:
        """Detect type of legal document (LUẬT, NGHỊ ĐỊNH, VĂN BẢN, etc)."""
        patterns = {
            "LUẬT": r"LUẬT\s+\d+/\d+",
            "NGHỊ ĐỊNH": r"NGHỊ\s+ĐỊNH\s+\d+/\d+",
            "THÔNG TƯ": r"THÔNG\s+TƯ\s+\d+/\d+",
            "VĂN BẢN HƯỚNG DẪN": r"VĂN\s+BẢN\s+HƯỚNG\s+DẪN",
            "QUYẾT ĐỊNH": r"QUYẾT\s+ĐỊNH\s+\d+/\d+",
            "CHỈ THỊ": r"CHỈ\s+THỊ\s+\d+/\d+",
        }
        
        for doc_type, pattern in patterns.items():
            if re.search(pattern, text):
                return doc_type
        
        return "VĂN BẢN PHÁP LÝ"

    @staticmethod
    def _detect_jurisdiction(text: str) -> str:
        """Detect jurisdiction (central/provincial level)."""
        central_patterns = ["Chính phủ", "Bộ trưởng", "Tổng cục", "Cục"]
        provincial_patterns = ["Sở", "Phòng", "Tỉnh", "Thành phố"]
        
        if re.search("|".join(central_patterns), text):
            return "TRUNG ƯƠNG"
        elif re.search("|".join(provincial_patterns), text):
            return "ĐỊA PHƯƠNG"
        
        return "KHÔNG XÁC ĐỊNH"
