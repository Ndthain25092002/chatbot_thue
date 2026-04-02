# Frontend

Trang web chat don gian de su dung Legal Chatbot.

## Chay nhanh

Tu thu muc workspace goc `app_luat`:

PowerShell:

	cd .\legal-chatbot\frontend
	python -m http.server 5500

Mo trinh duyet tai:

	http://127.0.0.1:5500

## Cach dung

- Mac dinh dang bat `Mock mode`, ban co the test UI ngay ca khi backend chua xong API.
- Neu da co API that, tat `Mock mode` va nhap `API base URL` (vi du `http://127.0.0.1:8000`).
- Nhan `Gui` de hoi dap, nhan `Clear` de xoa man hinh chat.

## File chinh

- `index.html`: khung trang web.
- `styles.css`: giao dien va responsive.
- `app.js`: logic chat (mock mode + goi API backend).
