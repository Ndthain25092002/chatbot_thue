const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chatForm");
const inputEl = document.getElementById("promptInput");
const mockModeEl = document.getElementById("mockMode");
const apiBaseEl = document.getElementById("apiBase");
const clearBtn = document.getElementById("clearBtn");

const sessionId = `web-${Date.now()}`;

function addMessage(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `message ${role}`;
  bubble.textContent = text;
  messagesEl.appendChild(bubble);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function getMockAnswer(query) {
  const q = query.toLowerCase();

  if (q.includes("thue") && q.includes("thu nhap")) {
    return [
      "Tom tat nhanh: Thue thu nhap ca nhan thuong duoc tinh theo thu nhap chiu thue sau khi tru cac khoan giam tru [S1].",
      "Ban can doi chieu them theo dieu khoan cu the trong van ban hien hanh [S2]."
    ].join("\n\n");
  }

  if (q.includes("le phi") || q.includes("phi")) {
    return [
      "Thong tin tham khao: Le phi va phi la hai nhom nghia vu tai chinh khac nhau ve ban chat va co quan thu [S1].",
      "Ban nen gui ro loai thu tuc de he thong tra loi sat hon [S2]."
    ].join("\n\n");
  }

  return [
    "Day la phan hoi mock mode de ban test UI ngay.",
    "Tat Mock mode de goi API that tu backend khi endpoint da san sang."
  ].join("\n\n");
}

async function askBackend(query) {
  const base = (apiBaseEl.value || "").trim().replace(/\/$/, "");
  if (!base) {
    throw new Error("API base URL dang rong");
  }

  const res = await fetch(`${base}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: query,
      message: query,
      session_id: sessionId
    })
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }

  const data = await res.json();
  return data.answer || data.response || JSON.stringify(data, null, 2);
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const prompt = inputEl.value.trim();
  if (!prompt) {
    return;
  }

  addMessage("user", prompt);
  inputEl.value = "";
  inputEl.focus();

  addMessage("bot", "Dang xu ly...");
  const loadingBubble = messagesEl.lastElementChild;

  try {
    const answer = mockModeEl.checked ? getMockAnswer(prompt) : await askBackend(prompt);
    loadingBubble.textContent = answer;
  } catch (error) {
    loadingBubble.textContent = `Khong goi duoc backend: ${error.message}`;
  }
});

clearBtn.addEventListener("click", () => {
  messagesEl.innerHTML = "";
  addMessage("bot", "Xin chao. Ban hay nhap cau hoi phap ly de bat dau.");
});

addMessage("bot", "Xin chao. Ban hay nhap cau hoi phap ly de bat dau.");
