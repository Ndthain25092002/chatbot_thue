# Legal Chatbot Architecture

## 1) Mục tiêu
- Xây dựng chatbot pháp lý theo mô hình RAG (Retrieval-Augmented Generation).
- Đảm bảo câu trả lời có nguồn trích dẫn, dễ kiểm soát chất lượng, và dễ mở rộng.

## 2) Cấu trúc thư mục
```
legal-chatbot/
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── api/
│   │   └── chat.py
│   ├── rag/
│   │   ├── retriever.py
│   │   ├── embedder.py
│   │   ├── generator.py
│   │   ├── reranker.py
│   ├── services/
│   │   ├── legal_service.py
│   │   ├── cache_service.py
│   ├── db/
│   │   ├── mongo.py
│   │   ├── faiss_index.py
│   ├── data_pipeline/
│   │   ├── crawler.py
│   │   ├── processor.py
│   │   ├── chunker.py
│   └── utils/
│       ├── logger.py
│       ├── text_cleaner.py
├── frontend/
└── models/
```

## 3) Trách nhiệm từng lớp
- `api`: nhận request, validate dữ liệu đầu vào, gọi service, trả response.
- `services`: điều phối nghiệp vụ (orchestration), cache, kiểm soát flow chính.
- `rag`: xử lý truy vấn semantic (embed, retrieve, rerank, generate).
- `db`: adapter cho MongoDB và FAISS.
- `data_pipeline`: ingest và chuẩn hóa dữ liệu pháp lý trước khi đánh chỉ mục.
- `utils`: các hàm dùng chung (log, làm sạch text).

## 4) Luồng dữ liệu chính
### 4.1 Ingestion
1. `crawler.py` thu thập văn bản pháp lý.
2. `processor.py` làm sạch, chuẩn hóa metadata.
3. `chunker.py` chia đoạn văn bản.
4. `embedder.py` tạo embedding cho mỗi chunk.
5. Lưu metadata vào MongoDB (`mongo.py`) và vector vào FAISS (`faiss_index.py`).

### 4.2 Chat Query
1. Client gọi API chat (`api/chat.py`).
2. `legal_service.py` kiểm tra cache (`cache_service.py`).
3. Nếu cache miss, `embedder.py` tạo embedding cho câu hỏi.
4. `retriever.py` tìm top-k chunks trong FAISS.
5. (Optional) `reranker.py` sắp xếp lại kết quả.
6. `generator.py` tạo câu trả lời từ ngữ cảnh tìm được.
7. Trả kết quả gồm `answer`, `sources`, `confidence`.

## 5) Quy ước mở rộng
- Bắt buộc gắn `source` cho mỗi đoạn context được dùng để trả lời.
- Tách rõ code hạ tầng (db, cache, llm sdk) khỏi logic nghiệp vụ.
- Hỗ trợ cấu hình qua biến môi trường trong `config.py`.
- Theo dõi log theo request-id để truy vết.

## 6) Gợi ý bước tiếp theo
- Chọn framework API (FastAPI hoặc Flask) và thay placeholder trong `app.py`.
- Tích hợp embedding model thực (sentence-transformers/OpenAI embeddings).
- Tích hợp LLM thực trong `generator.py` và template prompt có citation bắt buộc.
- Dùng Redis thay cache in-memory khi chạy production.
