// Chat frontend for the RAG WebSocket server (plain JavaScript).
//
// Protocol (must match src/server/server.py):
//   client -> server: {"prompt": "answer", "query": "<question>", "k": 5}
//   server -> client: {"answer": "<text>", "sources": [source, ...]}
//                 or: {"error": "<message>"}

const chat = document.getElementById("chat");
const empty = document.getElementById("empty");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendButton = document.getElementById("send");
const statusBadge = document.getElementById("status");
const DEFAULT_K = 5;

let socket = null;
let pendingBubble = null;
let thinkingTimer = null;
let reconnectTimer = null;
let reconnectDelay = 1000;

// Served by the Python server: connect to the same host.
// Opened as a local file: fall back to the default server address.
function serverUrl() {
    const { protocol, host } = window.location;
    if (protocol === "http:" || protocol === "https:") {
        return `${protocol === "https:" ? "wss:" : "ws:"}//${host}/ws`;
    }
    return "ws://localhost:8000/ws";
}

// ---------- Rendering ----------

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// Minimal markdown: ```code blocks```, `inline code`, **bold**, paragraphs.
// The text is escaped first, so the model output can never inject HTML.
function renderMarkdown(text) {
    const parts = escapeHtml(text.trim()).split("```");
    return parts
        .map((part, index) => {
            if (index % 2 === 1) {
                const code = part.replace(/^[\w-]*\n/, "");
                return `<pre><code>${code}</code></pre>`;
            }
            return part
                .split(/\n{2,}/)
                .filter((paragraph) => paragraph.trim() !== "")
                .map((paragraph) => {
                    const html = paragraph
                        .replace(/`([^`]+)`/g, "<code>$1</code>")
                        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
                        .replace(/\n/g, "<br>");
                    return `<p>${html}</p>`;
                })
                .join("");
        })
        .join("");
}

function scrollToBottom() {
    chat.scrollTop = chat.scrollHeight;
}

function addUserMessage(text) {
    empty.hidden = true;
    const message = document.createElement("div");
    message.className = "message user";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    message.appendChild(bubble);
    chat.appendChild(message);
    scrollToBottom();
}

function addAssistantMessage() {
    const message = document.createElement("div");
    message.className = "message assistant";
    message.innerHTML =
        '<div class="avatar">◆</div>' +
        '<div class="bubble"><div class="thinking">' +
        '<div class="typing"><span></span><span></span><span></span></div>' +
        '<span class="thinking-time">Thinking… 0.0s</span></div></div>';
    chat.appendChild(message);
    scrollToBottom();

    const bubble = message.querySelector(".bubble");
    const timeLabel = bubble.querySelector(".thinking-time");
    const start = performance.now();
    bubble.dataset.start = String(start);

    stopThinkingTimer();
    thinkingTimer = setInterval(() => {
        const seconds = (performance.now() - start) / 1000;
        timeLabel.textContent = `Thinking… ${seconds.toFixed(1)}s`;
    }, 100);

    return bubble;
}

function stopThinkingTimer() {
    clearInterval(thinkingTimer);
    thinkingTimer = null;
}

function thoughtLabel(bubble) {
    const seconds = (performance.now() - Number(bubble.dataset.start)) / 1000;
    return `<div class="thought">Thought for ${seconds.toFixed(1)}s</div>`;
}

function renderSources(sources) {
    if (!sources || sources.length === 0) {
        return "";
    }
    const items = sources
        .map((source) => {
            const shortPath = source.file_path.replace(/^data\/raw\/[^/]+\//, "");
            const range = `${source.first_character_index}–${source.last_character_index}`;
            return `<li title="${escapeHtml(source.file_path)}">` +
                `<span class="source-path">${escapeHtml(shortPath)}</span>` +
                `<span class="source-range">${range}</span></li>`;
        })
        .join("");
    return `<details class="sources"><summary>${sources.length} sources</summary>` +
        `<ul>${items}</ul></details>`;
}

function fillAssistantMessage(bubble, data) {
    stopThinkingTimer();
    const header = thoughtLabel(bubble);
    if (data.error !== undefined) {
        bubble.innerHTML = header +
            `<p class="error-text">${escapeHtml(String(data.error))}</p>`;
    } else {
        bubble.innerHTML = header +
            renderMarkdown(data.answer || "") + renderSources(data.sources);
    }
    scrollToBottom();
}

// ---------- Connection ----------

const STATUS_TEXT = {
    connecting: "Connecting…",
    open: "Connected",
    closed: "Disconnected",
};

function setStatus(state) {
    statusBadge.dataset.state = state;
    statusBadge.querySelector(".status-text").textContent = STATUS_TEXT[state];
    updateSendButton();
}

function connect() {
    clearTimeout(reconnectTimer);
    if (socket !== null) {
        socket.onclose = null;
        socket.close();
    }
    setStatus("connecting");

    try {
        socket = new WebSocket(serverUrl());
    } catch (error) {
        console.error(error);
        setStatus("closed");
        return;
    }

    socket.onopen = () => {
        reconnectDelay = 1000;
        setStatus("open");
    };

    socket.onmessage = (event) => {
        let data;
        try {
            data = JSON.parse(event.data);
        } catch {
            data = { error: "Received an invalid response from the server." };
        }
        if (pendingBubble !== null) {
            fillAssistantMessage(pendingBubble, data);
            pendingBubble = null;
        }
        updateSendButton();
    };

    socket.onclose = () => {
        setStatus("closed");
        if (pendingBubble !== null) {
            fillAssistantMessage(pendingBubble, {
                error: "Connection lost before an answer arrived.",
            });
            pendingBubble = null;
        }
        reconnectTimer = setTimeout(connect, reconnectDelay);
        reconnectDelay = Math.min(reconnectDelay * 2, 15000);
    };
}

// ---------- Sending ----------

function isConnected() {
    return socket !== null && socket.readyState === WebSocket.OPEN;
}

function updateSendButton() {
    sendButton.disabled =
        !isConnected() || pendingBubble !== null || input.value.trim() === "";
}

function sendQuestion(text) {
    const query = text.trim();
    if (query === "" || !isConnected() || pendingBubble !== null) {
        return;
    }

    addUserMessage(query);
    pendingBubble = addAssistantMessage();
    socket.send(JSON.stringify({ prompt: "answer", query: query, k: DEFAULT_K }));

    input.value = "";
    autoResize();
    updateSendButton();
}

function autoResize() {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 200)}px`;
}

// ---------- Events ----------

form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendQuestion(input.value);
});

input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        sendQuestion(input.value);
    }
});

input.addEventListener("input", () => {
    autoResize();
    updateSendButton();
});

document.querySelectorAll(".suggestion").forEach((button) => {
    button.addEventListener("click", () => sendQuestion(button.textContent));
});

connect();
input.focus();
