# RUN GUIDE

Tai lieu nay tong hop nhanh cac lenh chay:
- Demo nhanh
- Chay that (co model sinh cau tra loi qua Ollama)
- Chay end-to-end test pipeline

## 1) Chuan bi moi truong

Tu thu muc workspace goc `app_luat`:

PowerShell:

    .\.venv\Scripts\Activate.ps1
    pip install -r .\legal-chatbot\requirements.txt

Neu ban dung lan dau, model embedding se duoc tai tu Hugging Face khi chay.

## 2) Lenh chay demo (terminal chat)

Tu thu muc `legal-chatbot/backend`:

PowerShell:

    cd .\legal-chatbot\backend
    python demo_terminal_chat.py

Ghi chu:
- Script se tu dong ingest du lieu mau neu FAISS index dang rong.
- File du lieu mac dinh: `data/tax_fee_legal_documents.json`.
- Thoat demo bang `/exit`.

## 3) Lenh chay that (chat voi Ollama that)

Muc nay dung cho tra loi bang model LLM that (khong fallback tom tat).

### 3.1 Khoi dong Ollama va tai model

Chay tren may local (terminal khac):

    ollama serve
    ollama pull qwen2:7b

### 3.2 Dat bien moi truong (neu can)

PowerShell:

    $env:OLLAMA_BASE_URL = "http://localhost:11434"
    $env:GENERATOR_MODEL = "qwen2:7b"

### 3.3 Chay chat that

Tu thu muc `legal-chatbot/backend`:

PowerShell:

    cd .\legal-chatbot\backend
    python demo_terminal_chat.py

Neu Ollama khong chay, he thong van tra loi theo che do fallback context.

## 4) Lenh chay ingest du lieu that

Tu thu muc `legal-chatbot/backend`:

PowerShell:

    cd .\legal-chatbot\backend
    python run_ingest_real_json.py

Script nay rebuild index tu JSON that trong `data/tax_fee_legal_documents.json`.

## 5) Lenh chay end-to-end

Tu thu muc `legal-chatbot/backend`:

PowerShell:

    cd .\legal-chatbot\backend
    python test_e2e_pipeline.py

E2E test bao gom:
- chunk -> embed -> index -> retrieve
- In ket qua retrieval de xac nhan pipeline hoat dong.

## 6) Lenh chay API backend that (FastAPI)

Backend da co endpoint `POST /chat` va `GET /health`.

Tu thu muc `legal-chatbot/backend`:

PowerShell:

    cd .\legal-chatbot\backend
    uvicorn app:app --host 127.0.0.1 --port 8000 --reload

Test nhanh health:

    Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/health"

Test nhanh chat:

    $body = @{ user_query = "Le phi truoc ba la gi?"; session_id = "demo-web" } | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/chat" -ContentType "application/json" -Body $body

Ghi chu:
- Frontend web page co the goi API nay voi `API base URL = http://127.0.0.1:8000`.
- Payload chap nhan ca `user_query` hoac `message`.
