# Legal Chatbot Ingestion Pipeline

## Overview
Pipeline để tải, xử lý, và lưu trữ văn bản pháp lý Việt Nam từ Hugging Face dataset.

## Cấu trúc luồng xử lý
1. **Crawler** → Tải dữ liệu từ `th1nhng0/vietnamese-legal-documents` trên Hugging Face
2. **Processor** → Làm sạch text, trích xuất metadata (loại văn bản, cấp chính quyền)
3. **Chunker** → Chia văn bản thành các chunk (800 tokens, overlap 120)
4. **Embedder** → Tạo vector embedding cho mỗi chunk
5. **Storage** → Lưu vào MongoDB (metadata) và FAISS (vector search)

## Cách chạy

### 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 2. Chạy pipeline ingestion
```bash
cd backend
python -m data_pipeline.ingest_pipeline
```

### 3. Kết quả
- Logs chi tiết từng bước processing
- File mẫu chunks được lưu tại `./data/processed_chunks_sample.json`

## Cấu trúc dữ liệu output

Mỗi chunk sau khi processing:
```json
{
  "document_source": "content__0",
  "chunk_index": 0,
  "content": "Nội dung văn bản pháp lý...",
  "metadata": {
    "document_type": "LUẬT",
    "jurisdiction": "TRUNG ƯƠNG",
    "word_count": 150,
    "content_length": 890,
    "found_dates": ["01/01/2023"]
  },
  "embedding": [0.123, 0.456, ...]  // Vector embedding
}
```

## Các class chính

### Crawler
- `crawl_from_hf_dataset()` → Tải từ Hugging Face
- Hỗ trợ multiple splits (train/test/validation)
- Tự động trích xuất content từ các field phổ thông

### Processor  
- `process()` → Xử lý batch documents
- Làm sạch HTML, URL, email; chuẩn hóa spacing
- Tự động detect loại văn bản (LUẬT, NGHỊ ĐỊNH, etc)
- Tự động detect cấp chính quyền (TRUNG ƯƠNG / ĐỊA PHƯƠNG)

### Chunker
- `chunk_text()` → Chia text thành chunks
- Hỗ trợ tùy chỉnh `chunk_size` và `chunk_overlap`

## Ghi chú
- Pipeline hiện dùng embedder placeholder (trả vector 384-dim zeros)
- Tích hợp embedding model thực (sentence-transformers, OpenAI) vào `backend/rag/embedder.py`
- Database storage hiện chỉ là placeholder, cần tích hợp MongoDB/FAISS thực
