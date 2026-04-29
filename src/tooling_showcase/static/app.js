const MODEL_PROFILES = [
  { model: "qwen3:8b", category: "general", job: "default everyday assistant", summary: "Best overall balance for normal daily requests.", chat_capable: true },
  { model: "qwen3.5:9b", category: "coding", job: "coding and technical implementation", summary: "Best coding model left in the local set.", chat_capable: true },
  { model: "mistral-nemo:12b", category: "linux", job: "linux troubleshooting and sysadmin help", summary: "Strong Linux and debugging profile with good speed.", chat_capable: true },
  { model: "qwen2.5:14b-instruct", category: "reasoning", job: "deep research, document-heavy analysis, and serious assistant work", summary: "Strong reasoning, long-context, and summary performance.", chat_capable: true },
  { model: "llama3.2:latest", category: "fast", job: "fast general responses", summary: "Fastest useful model left for quick replies.", chat_capable: true },
  { model: "dolphin3:latest", category: "summary", job: "quick summaries and casual chat", summary: "Best summary-focused fast model, with weaker reasoning control.", chat_capable: true },
  { model: "phi4:14b", category: "roleplay", job: "companion-style and personality-heavy conversations", summary: "Strongest tone, personality, and companion-style responses.", chat_capable: true },
  { model: "qwen2.5vl:7b", category: "vision", job: "image and mixed vision-text workflows", summary: "Use when screenshots, photos, or visual analysis matter.", chat_capable: true },
  { model: "nomic-embed-text:latest", category: "embedding", job: "primary embedding generation for retrieval and RAG", summary: "Embedding-only model, not for chat responses.", chat_capable: false },
  { model: "embeddinggemma:latest", category: "embedding", job: "secondary embedding generation for retrieval experiments", summary: "Embedding-only model, not for chat responses.", chat_capable: false }
];

const TOOL_EXAMPLES = {
  adapter_inventory: {},
  build_index: {},
  content_search: { query: "ToolRuntime" },
  file_search: { query: "README" },
  library_info: {},
  library_read_epub: { id: "", query: "", max_chars: 12000 },
  library_read_zim: { id: "", title: "" },
  library_search: { query: "local models", limit: 10 },
  query_index: { query: "routing and tool catalog" },
  read_file: { path: "README.md" },
  shell_command: { command: "git status" },
  tree_view: { path: ".", max_depth: 4 },
  web_search: { query: "Ollama structured outputs" }
};

const TOOL_DOCS = {
  adapter_inventory: { name: "Adapter Inventory", safety: "read-only", summary: "Show which workspace adapters are detected and usable.", usage: "Use this when you want provenance, workspace status, or adapter summaries." },
  build_index: { name: "Build Index", safety: "read/write state", summary: "Build the lightweight local index from text files.", usage: "Run after a big repo change or before repeated codebase questions." },
  content_search: { name: "Content Search", safety: "read-only", summary: "Search file contents for a string or symbol.", usage: "Useful for locating functions, prompts, routes, or feature flags." },
  file_search: { name: "File Search", safety: "read-only", summary: "Find files by filename.", usage: "Use before read_file when you know part of a filename but not the exact path." },
  library_info: { name: "Library Info", safety: "read-only", summary: "Show configured local library sources.", usage: "Use to confirm EPUB/ZIM library availability." },
  library_read_epub: { name: "Read EPUB", safety: "read-only", summary: "Read a selected EPUB item or matching passage.", usage: "Requires a library item id from library_search." },
  library_read_zim: { name: "Read ZIM", safety: "read-only", summary: "Read a local ZIM article by id/title.", usage: "Useful for offline docs or knowledge bases." },
  library_search: { name: "Library Search", safety: "read-only", summary: "Search the local library catalog.", usage: "Use before reading EPUB/ZIM content." },
  query_index: { name: "Query Index", safety: "read-only", summary: "Search the built local index.", usage: "Best for repo-level questions after build_index has run." },
  read_file: { name: "Read File", safety: "read-only", summary: "Read a local text file.", usage: "Use with an exact path from file_search or tree_view." },
  shell_command: { name: "Shell Command", safety: "guarded", summary: "Run a shell command with blocked and confirm-required patterns.", usage: "Use only for explicit terminal tasks like git status, tests, or safe inspection." },
  tree_view: { name: "Tree View", safety: "read-only", summary: "Show a shallow project tree.", usage: "Good for quickly understanding project layout." },
  web_search: { name: "Web Search", safety: "network", summary: "Run a simple web lookup.", usage: "Use for docs, current info, or external references." }
};

const ROUTE_PATTERNS = [
  ["vision", /\b(image|photo|picture|screenshot|diagram|chart|graph|ocr|scan|visual|vision)\b/i],
  ["roleplay", /\b(roleplay|pretend|character|persona|companion|romance|flirt|story|fiction|in character)\b/i],
  ["reasoning", /\b(embedding|embeddings|rag|semantic search|vector search|retrieve|retrieval|compare|comparison|tradeoff|trade-off|analyze|analysis|architecture|design|proposal|research|investigate|why|reasoning|document|pdf|spec|report|long context|evidence)\b/i],
  ["summary", /\b(summary|summarize|summarise|tldr|tl;dr|recap|condense|short version|brief summary)\b/i],
  ["coding", /\b(code|coding|program|function|class|method|refactor|debug|bug|stack trace|exception|pytest|unit test|integration test|lint|format|compile|typescript|javascript|python|rust|golang|go|sql|regex|api)\b/i],
  ["linux", /\b(linux|arch|ubuntu|debian|fedora|systemd|journalctl|bash|shell|ssh|docker|podman|kernel|grub|pacman|apt|dnf|fstab|mount|service file|sysadmin)\b/i],
  ["fast", /\b(quick|quickly|fast|faster|brief|briefly|one-liner|one line)\b/i]
];

const DEFAULT_SETTINGS = {
  density: "comfortable",
  stream: true,
  confirm: false,
  attachMemories: true,
  autoScroll: true,
  enableThinking: true,
  openThinking: false,
  detailsEnabled: true,
  compactTools: false,
  journalLimit: 50,
  messageWidth: 78,
  memoryPrefix: "Relevant local UI memories",
  responseFormat: "",
  modelOptions: {
    temperature: 0.2,
    num_ctx: 4096,
    top_p: 0.95,
    top_k: 40,
    repeat_penalty: 1.1,
    seed: -1,
    num_predict: -1,
    keep_alive: "",
    stop: []
  }
};

const PAGE_META = {
  chat: {
    eyebrow: "Chat",
    title: "Assistant thread",
    summary: "Ask questions, inspect files, and let tools run in the background."
  },
  sessions: {
    eyebrow: "State",
    title: "Sessions and memories",
    summary: "Manage browser-local chat history and reusable notes."
  },
  tools: {
    eyebrow: "Runtime",
    title: "Manual tool console",
    summary: "Run explicit tools for debugging, inspection, and verification."
  },
  adapters: {
    eyebrow: "Workspace",
    title: "Adapters",
    summary: "Inspect connected source workspaces and reference projects."
  },
  journal: {
    eyebrow: "Observability",
    title: "Journal",
    summary: "Review backend events, tool calls, and autonomous-run traces."
  }
};

const STORAGE_KEYS = {
  sessions: "showcase.ui.sessions.v3",
  activeSession: "showcase.ui.activeSession.v3",
  memories: "showcase.ui.memories.v3",
  settings: "showcase.ui.settings.v3",
  systemPrompt: "showcase.ui.systemPrompt.v3"
};

const state = {
  sessions: [],
  activeSessionId: null,
  memories: [],
  models: [],
  tools: [],
  toolCards: [],
  adapters: [],
  journal: [],
  journalStats: {},
  settings: structuredClone(DEFAULT_SETTINGS),
  busy: false,
  lastController: null,
  pendingConfirm: null,
  detailPayload: null,
  activePage: "chat"
};

const $ = (id) => document.getElementById(id);
const chatLog = $("chatLog");
const template = $("messageTemplate");

function uid(prefix = "id") {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function prettyBytes(bytes) {
  if (!Number.isFinite(Number(bytes)) || Number(bytes) <= 0) return "unknown size";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = Number(bytes);
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  return `${size.toFixed(size >= 10 || unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function stripThinkTags(text) {
  return String(text ?? "").replace(/<think>[\s\S]*?<\/think>/gi, "").trim();
}

function extractThinkText(text) {
  const chunks = [];
  const regex = /<think>([\s\S]*?)<\/think>/gi;
  let match;
  while ((match = regex.exec(String(text ?? "")))) chunks.push(match[1].trim());
  return chunks.join("\n\n");
}

function wordCount(text) {
  const words = String(text ?? "").trim().match(/\S+/g);
  return words ? words.length : 0;
}

function roughTokens(text) {
  return Math.ceil(String(text ?? "").length / 4);
}

function routeModelForText(text) {
  for (const [category, pattern] of ROUTE_PATTERNS) {
    if (pattern.test(text)) return MODEL_PROFILES.find((profile) => profile.category === category && profile.chat_capable);
  }
  return MODEL_PROFILES.find((profile) => profile.category === "general");
}

function activeSession() {
  return state.sessions.find((session) => session.id === state.activeSessionId) ?? state.sessions[0];
}

function deepMerge(base, override) {
  const result = structuredClone(base);
  for (const [key, value] of Object.entries(override || {})) {
    if (value && typeof value === "object" && !Array.isArray(value) && typeof result[key] === "object") {
      result[key] = deepMerge(result[key], value);
    } else {
      result[key] = value;
    }
  }
  return result;
}

function persist() {
  syncSettingsFromMainControls();
  localStorage.setItem(STORAGE_KEYS.sessions, JSON.stringify(state.sessions));
  localStorage.setItem(STORAGE_KEYS.activeSession, state.activeSessionId ?? "");
  localStorage.setItem(STORAGE_KEYS.memories, JSON.stringify(state.memories));
  localStorage.setItem(STORAGE_KEYS.settings, JSON.stringify(state.settings));
  localStorage.setItem(STORAGE_KEYS.systemPrompt, $("systemPromptInput").value);
}

function loadLocalState() {
  const oldSessions = localStorage.getItem("showcase.ui.sessions.v2");
  const oldActive = localStorage.getItem("showcase.ui.activeSession.v2");
  const oldMemories = localStorage.getItem("showcase.ui.memories.v2");
  const oldSettingsPrompt = localStorage.getItem("showcase.ui.systemPrompt.v2");
  try { state.sessions = JSON.parse(localStorage.getItem(STORAGE_KEYS.sessions) || oldSessions || "[]"); } catch { state.sessions = []; }
  try { state.memories = JSON.parse(localStorage.getItem(STORAGE_KEYS.memories) || oldMemories || "[]"); } catch { state.memories = []; }
  try { state.settings = deepMerge(DEFAULT_SETTINGS, JSON.parse(localStorage.getItem(STORAGE_KEYS.settings) || "{}")); } catch { state.settings = structuredClone(DEFAULT_SETTINGS); }
  state.activeSessionId = localStorage.getItem(STORAGE_KEYS.activeSession) || oldActive || null;
  $("systemPromptInput").value = localStorage.getItem(STORAGE_KEYS.systemPrompt) || oldSettingsPrompt || "";
  applySettingsToMainControls();
  if (!state.sessions.length) createSession(false);
  if (!activeSession()) state.activeSessionId = state.sessions[0].id;
}

function createSession(render = true) {
  const session = { id: uid("session"), title: "New session", createdAt: new Date().toISOString(), messages: [] };
  state.sessions.unshift(session);
  state.activeSessionId = session.id;
  persist();
  if (render) renderAll();
  return session;
}

function updateSessionTitle(session, text) {
  if (!session || session.title !== "New session") return;
  const cleaned = text.replace(/\s+/g, " ").trim();
  session.title = cleaned.length > 42 ? `${cleaned.slice(0, 42)}…` : cleaned || "New session";
}
function renameSession(sessionId) {
  const session = state.sessions.find((candidate) => candidate.id === sessionId);
  if (!session) return;
  const nextTitle = prompt("Rename session:", session.title || "New session");
  if (nextTitle === null) return;
  const cleaned = nextTitle.trim().replace(/\s+/g, " ");
  if (!cleaned) return;
  session.title = cleaned.length > 80 ? `${cleaned.slice(0, 80)}…` : cleaned;
  persist();
  renderAll();
}

function requestDeleteSession(sessionId) {
  const session = state.sessions.find((candidate) => candidate.id === sessionId);
  if (!session) return;
  openConfirmDialog({
    title: "Delete session?",
    message: `This deletes “${session.title || "Untitled session"}” and its ${session.messages?.length || 0} messages from browser storage.`,
    confirmText: "Delete session",
    onConfirm: () => deleteSession(sessionId)
  });
}

function deleteSession(sessionId) {
  if (state.sessions.length <= 1) {
    state.sessions = [];
    createSession(false);
  } else {
    const index = state.sessions.findIndex((session) => session.id === sessionId);
    state.sessions = state.sessions.filter((session) => session.id !== sessionId);
    if (state.activeSessionId === sessionId) {
      state.activeSessionId = state.sessions[Math.max(0, index - 1)]?.id || state.sessions[0]?.id || null;
    }
  }
  persist();
  renderAll();
}

function requestDeleteAllSessions() {
  openConfirmDialog({
    title: "Delete all sessions?",
    message: `This removes all ${state.sessions.length} local browser sessions and creates one empty replacement session. Memories, settings, and backend journal entries are untouched.`,
    confirmText: "Delete all sessions",
    onConfirm: deleteAllSessions
  });
}

function deleteAllSessions() {
  state.sessions = [];
  createSession(false);
  persist();
  renderAll();
}


function addSessionMessage(role, content, extra = {}) {
  const session = activeSession();
  const message = {
    id: uid("msg"),
    role,
    content: content ?? "",
    thinking: extra.thinking ?? "",
    toolCalls: extra.toolCalls ?? [],
    createdAt: new Date().toISOString(),
    ok: extra.ok ?? true,
    model: extra.model ?? null,
    options: extra.options ?? null,
    modelRoute: extra.modelRoute ?? null,
    latencyMs: extra.latencyMs ?? null
  };
  session.messages.push(message);
  if (role === "user") updateSessionTitle(session, content);
  persist();
  renderSessions();
  renderSessionTitle();
  renderSidebarOverview();
  return message;
}

function renderAll() {
  renderSessions();
  renderMemories();
  renderChat();
  updatePageChrome();
  applySettingsVisuals();
}

function renderSessionTitle() {
  const session = activeSession();
  const meta = PAGE_META[state.activePage] || PAGE_META.chat;
  $("pageEyebrow").textContent = meta.eyebrow;
  $("sessionTitle").textContent = state.activePage === "chat" ? (session?.title || "New session") : meta.title;
  $("pageSummary").textContent = meta.summary;
}

function updatePageChrome() {
  renderSessionTitle();
  document.querySelectorAll("[data-page]").forEach((page) => {
    page.classList.toggle("active", page.dataset.page === state.activePage);
  });
  document.querySelectorAll("[data-page-target]").forEach((button) => {
    button.classList.toggle("active", button.dataset.pageTarget === state.activePage);
  });
  renderSidebarOverview();
}

function setActivePage(pageName, { closeDrawer = true } = {}) {
  state.activePage = PAGE_META[pageName] ? pageName : "chat";
  updatePageChrome();
  if (state.activePage === "journal") loadJournal();
  if (state.activePage === "adapters") loadAdapters();
  if (closeDrawer) closeMobileDrawers();
}

function renderSidebarOverview() {
  const root = $("sidebarOverview");
  if (!root) return;
  const session = activeSession();
  const messages = state.sessions.reduce((sum, item) => sum + (item.messages?.length || 0), 0);
  const toolCalls = state.sessions.reduce((sum, item) => sum + (item.messages || []).reduce((inner, msg) => inner + (msg.toolCalls || []).length, 0), 0);
  root.innerHTML = `
    <div class="overview-tile"><strong>${state.sessions.length}</strong><span>sessions</span></div>
    <div class="overview-tile"><strong>${messages}</strong><span>messages</span></div>
    <div class="overview-tile"><strong>${state.tools.length || "-"}</strong><span>tools</span></div>
    <div class="overview-tile"><strong>${state.journal.length || "-"}</strong><span>events loaded</span></div>
    <div class="overview-tile"><strong>${state.memories.length}</strong><span>memories</span></div>
    <div class="overview-tile"><strong>${toolCalls}</strong><span>tool calls</span></div>`;
  root.title = session?.title ? `Active session: ${session.title}` : "No active session";
}

function renderSessions() {
  const root = $("sessionList");
  root.innerHTML = "";
  state.sessions.forEach((session) => {
    const item = document.createElement("div");
    item.className = `session-item clickable-card ${session.id === state.activeSessionId ? "active" : ""}`;
    const count = session.messages.length;
    const updated = session.messages.at(-1)?.createdAt || session.createdAt;
    item.innerHTML = `
      <button class="session-main" data-action="open" title="Open session">
        <strong>${escapeHtml(session.title)}</strong>
        <span>${count} messages · ${new Date(updated).toLocaleString()}</span>
      </button>
      <div class="session-actions">
        <button class="ghost-button" data-action="details" title="Show session details">Details</button>
        <button class="ghost-button" data-action="rename" title="Rename session">Rename</button>
        <button class="danger-button" data-action="delete" title="Delete session">Delete</button>
      </div>`;
    item.querySelector("[data-action=\"open\"]").addEventListener("click", (event) => {
      if (event.altKey) return openSessionDetail(session);
      state.activeSessionId = session.id;
      persist();
      renderAll();
      setActivePage("chat");
    });
    item.querySelector("[data-action=\"details\"]").addEventListener("click", (event) => { event.stopPropagation(); openSessionDetail(session); });
    item.querySelector("[data-action=\"rename\"]").addEventListener("click", (event) => { event.stopPropagation(); renameSession(session.id); });
    item.querySelector("[data-action=\"delete\"]").addEventListener("click", (event) => { event.stopPropagation(); requestDeleteSession(session.id); });
    item.addEventListener("dblclick", () => openSessionDetail(session));
    root.appendChild(item);
  });
}

function renderMemories() {
  const root = $("memoryList");
  root.innerHTML = "";
  if (!state.memories.length) {
    root.innerHTML = `<div class="memory-item clickable-card"><span>No local UI memories yet. Add stable preferences or project notes here.</span></div>`;
    root.firstElementChild?.addEventListener("click", () => openCollectionDetail("Memory", "No local memories yet.", { memories: [] }));
    renderSidebarOverview();
    return;
  }
  state.memories.forEach((memory) => {
    const item = document.createElement("div");
    item.className = "memory-item clickable-card";
    item.innerHTML = `
      <strong>${escapeHtml(memory.title || "Memory")}</strong>
      <span>${escapeHtml(memory.text)}</span>
      <div class="memory-actions">
        <button class="ghost-button" data-action="pin">${memory.pinned ? "Pinned" : "Pin"}</button>
        <button class="danger-button" data-action="delete">Delete</button>
      </div>`;
    item.addEventListener("click", () => openMemoryDetail(memory));
    item.querySelector('[data-action="pin"]').addEventListener("click", (event) => {
      event.stopPropagation();
      memory.pinned = !memory.pinned;
      state.memories.sort((a, b) => Number(Boolean(b.pinned)) - Number(Boolean(a.pinned)));
      persist();
      renderMemories();
    });
    item.querySelector('[data-action="delete"]').addEventListener("click", (event) => {
      event.stopPropagation();
      state.memories = state.memories.filter((candidate) => candidate.id !== memory.id);
      persist();
      renderMemories();
    });
    root.appendChild(item);
  });
  renderSidebarOverview();
}

function renderChat() {
  const session = activeSession();
  chatLog.innerHTML = "";
  if (!session?.messages.length) {
    chatLog.innerHTML = `
      <div class="empty-state clickable-card" id="emptyChatState">
        <strong>Ready when you are.</strong>
        <span>Start with a focused request. Presets disappear after the first message so the thread stays clean.</span>
        <div class="starter-grid" aria-label="Starter prompts">
          <button class="starter-card" data-preset="code"><strong>Review code</strong><small>Find bugs, risks, and exact fixes in a file or design.</small></button>
          <button class="starter-card" data-preset="linux"><strong>Diagnose Linux</strong><small>Work through shell, kernel, service, or package issues.</small></button>
          <button class="starter-card" data-preset="research"><strong>Research path</strong><small>Compare tradeoffs and produce an implementation plan.</small></button>
          <button class="starter-card" data-preset="structure"><strong>Inspect project</strong><small>Look around the repo structure before answering.</small></button>
        </div>
      </div>`;
    $("emptyChatState")?.addEventListener("click", (event) => {
      if (event.target.closest("button")) return;
      openSessionDetail(session);
    });
    return;
  }
  session.messages.forEach((message) => renderMessage(message));
  scrollChat();
}

function renderMessage(message) {
  const node = template.content.firstElementChild.cloneNode(true);
  node.classList.add(message.role);
  node.dataset.messageId = message.id;
  node.querySelector(".message-role").textContent = message.role === "user" ? "You" : message.role === "tool" ? "Tool" : "Assistant";
  node.querySelector(".message-time").textContent = new Date(message.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  node.querySelector(".message-content").textContent = message.content || "";
  renderActivityBox(node, message);
  node.querySelector(".copy-message").addEventListener("click", async (event) => {
    event.stopPropagation();
    await navigator.clipboard.writeText(`${message.content || ""}${message.thinking ? `\n\n[Thinking]\n${message.thinking}` : ""}`);
  });
  node.querySelector(".message-details").addEventListener("click", (event) => {
    event.stopPropagation();
    openMessageDetail(message);
  });
  node.addEventListener("click", (event) => {
    if (!state.settings.detailsEnabled) return;
    if (event.target.closest("button, details, summary, pre")) return;
    openMessageDetail(message);
  });
  chatLog.appendChild(node);
  return node;
}

function renderActivityBox(node, message) {
  const box = node.querySelector(".activity-box");
  const title = node.querySelector(".activity-title");
  const meta = node.querySelector(".activity-meta");
  const thinkingContent = node.querySelector(".thinking-content");
  const toolsRoot = node.querySelector(".activity-tool-stack");
  const calls = message.toolCalls || [];
  const hasThinking = Boolean(String(message.thinking || "").trim());
  const hasTools = calls.length > 0;

  if (!hasThinking && !hasTools) {
    box.hidden = true;
    return;
  }

  box.hidden = false;
  box.open = false;
  title.textContent = hasThinking ? (hasTools ? "Thinking + tool use" : "Thinking") : "Tool use";
  meta.textContent = hasTools ? `${calls.length} tool${calls.length === 1 ? "" : "s"}` : "";
  thinkingContent.hidden = !hasThinking;
  thinkingContent.textContent = hasThinking ? formatActivityThinking(message.thinking, calls) : "";
  renderToolCalls(toolsRoot, calls, { nested: true });
}

function formatActivityThinking(thinking, calls) {
  const text = String(thinking || "").trim();
  if (!calls.length) return text;
  const toolSummary = calls
    .map((call, index) => `(tool use ${index + 1}: ${call.tool_name || call.name || "tool"} ${call.ok ? "ok" : "failed"})`)
    .join("\n");
  if (!text) return toolSummary;
  return `${text}\n\n${toolSummary}`;
}

function renderToolCalls(root, calls, { nested = false } = {}) {
  root.innerHTML = "";
  calls.forEach((call) => {
    const card = document.createElement(nested ? "details" : "section");
    card.className = `tool-call clickable-card${nested ? " nested-tool-call" : ""}`;
    const summary = escapeHtml(call.summary || JSON.stringify(call.data ?? call, null, 2));
    const payload = escapeHtml(JSON.stringify(call, null, 2));
    card.innerHTML = `
      ${nested
        ? `<summary><strong>${escapeHtml(call.tool_name || call.name || "tool")}</strong><span class="${call.ok ? "ok-text" : "bad-text"}">${call.ok ? "ok" : "failed"}</span></summary>`
        : `<header><strong>${escapeHtml(call.tool_name || call.name || "tool")}</strong><span class="${call.ok ? "ok-text" : "bad-text"}">${call.ok ? "ok" : "failed"}</span></header>`}
      <pre>${summary}</pre>
      <details class="tool-json-box"><summary>JSON</summary><pre>${payload}</pre></details>`;
    card.addEventListener("click", (event) => {
      if (event.target.closest("summary") || event.target.closest(".tool-json-box")) return;
      event.stopPropagation();
      openToolCallDetail(call);
    });
    root.appendChild(card);
  });
}

function scrollChat() {
  if ($("autoScrollToggle").checked) chatLog.scrollTop = chatLog.scrollHeight;
}

async function loadModels() {
  const select = $("modelSelect");
  select.innerHTML = `<option value="">Auto route</option>`;
  let liveModels = [];
  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    liveModels = Array.isArray(data.models) ? data.models : [];
    state.models = liveModels;
    $("modelStatus").textContent = data.ok ? `${liveModels.length} local` : "offline";
    $("modelStatus").className = `status-pill ${data.ok ? "ok" : "bad"}`;
    if (!data.ok && data.error) renderModelMeta(`Ollama models could not be loaded: ${data.error}`);
  } catch (error) {
    $("modelStatus").textContent = "offline";
    $("modelStatus").className = "status-pill bad";
    renderModelMeta(`Model endpoint unavailable: ${error.message}`);
  }

  const seen = new Set();
  for (const model of liveModels) {
    const name = model.name || model.model;
    if (!name || seen.has(name)) continue;
    seen.add(name);
    const option = document.createElement("option");
    option.value = name;
    option.textContent = `${name} ${model.size ? `· ${prettyBytes(model.size)}` : ""}`;
    select.appendChild(option);
  }

  const group = document.createElement("optgroup");
  group.label = "Suggested profiles";
  MODEL_PROFILES.forEach((profile) => {
    if (seen.has(profile.model)) return;
    const option = document.createElement("option");
    option.value = profile.model;
    option.disabled = !profile.chat_capable;
    option.textContent = `${profile.model} · ${profile.category}${profile.chat_capable ? "" : " · embedding only"}`;
    group.appendChild(option);
  });
  select.appendChild(group);
  updateModelMeta();
}

function renderModelMeta(message = "") {
  const root = $("modelMeta");
  if (message) {
    root.innerHTML = `<div class="model-card clickable-card"><span>${escapeHtml(message)}</span></div>`;
    return;
  }
  updateModelMeta();
}

function updateModelMeta() {
  const value = $("modelSelect").value;
  const profile = MODEL_PROFILES.find((item) => item.model === value) || null;
  const live = state.models.find((item) => item.name === value || item.model === value) || null;
  const root = $("modelMeta");
  if (!value) {
    root.innerHTML = `<div class="model-card clickable-card"><strong>Auto route</strong><span>UI previews the likely profile from your prompt, then leaves server-side routing alone unless you pick a model.</span></div>`;
  } else {
    root.innerHTML = `
      <div class="model-card clickable-card">
        <strong>${escapeHtml(value)}</strong>
        <span>${escapeHtml(profile?.summary || "Local Ollama model")}</span>
        <span>${escapeHtml(profile?.job || live?.details?.family || "")}</span>
        <span>${live?.size ? escapeHtml(prettyBytes(live.size)) : "Not found in live Ollama tags yet"}</span>
      </div>`;
  }
  root.querySelector(".model-card")?.addEventListener("click", () => openModelDetail(value));
}

function populateSettingsModelSelect() {
  const select = $("settingsModelSelect");
  if (!select) return;
  const current = $("modelSelect")?.value || "";
  select.innerHTML = '<option value="">Auto route</option>';
  const seen = new Set();
  state.models.filter((model) => model.chat_capable !== false).forEach((model) => {
    const name = model.name || model.model;
    if (!name || seen.has(name)) return;
    seen.add(name);
    const option = document.createElement("option");
    option.value = name;
    option.textContent = `${name}${model.category ? ` · ${model.category}` : model.size ? ` · ${prettyBytes(model.size)}` : ""}`;
    select.appendChild(option);
  });
  MODEL_PROFILES.filter((profile) => profile.chat_capable && !seen.has(profile.model)).forEach((profile) => {
    const option = document.createElement("option");
    option.value = profile.model;
    option.textContent = `${profile.model} · ${profile.category}`;
    select.appendChild(option);
  });
  select.value = current;
}

async function loadTools() {
  try {
    const res = await fetch("/api/tools");
    const data = await res.json();
    state.tools = Array.isArray(data.tools) ? data.tools : [];
    state.toolCards = Array.isArray(data.tool_cards) ? data.tool_cards : state.tools.map((tool) => ({ id: tool }));
  } catch {
    state.tools = Object.keys(TOOL_EXAMPLES);
    state.toolCards = state.tools.map((tool) => ({ id: tool }));
  }
  if (!state.tools.length) state.tools = Object.keys(TOOL_EXAMPLES);
  if (!state.toolCards.length) state.toolCards = state.tools.map((tool) => ({ id: tool }));
  renderTools();
  renderSidebarOverview();
}

function toolId(tool) {
  return typeof tool === "string" ? tool : (tool.id || tool.tool_id || tool.name || "tool");
}

function toolCardFor(id) {
  return state.toolCards.find((card) => toolId(card) === id) || { id, ...(TOOL_DOCS[id] || {}) };
}

function renderTools() {
  const select = $("toolSelect");
  select.innerHTML = "";
  state.tools.forEach((tool) => {
    const id = toolId(tool);
    const option = document.createElement("option");
    option.value = id;
    option.textContent = id;
    select.appendChild(option);
  });
  $("toolCount").textContent = String(state.tools.length);
  const list = $("toolList");
  list.innerHTML = "";
  state.tools.forEach((tool) => {
    const id = toolId(tool);
    const doc = { ...(TOOL_DOCS[id] || {}), ...toolCardFor(id) };
    const item = document.createElement("div");
    item.className = "tool-item clickable-card";
    item.innerHTML = `<code>${escapeHtml(id)}</code><span>${escapeHtml(doc.safety || (id === "shell_command" ? "guarded" : "ready"))}</span>`;
    item.addEventListener("click", () => {
      select.value = id;
      updateToolExample();
      openToolDetail(id);
    });
    list.appendChild(item);
  });
  updateToolExample();
}

function updateToolExample() {
  const tool = $("toolSelect").value;
  $("toolArgs").value = JSON.stringify(TOOL_EXAMPLES[tool] ?? {}, null, 2);
}

async function loadAdapters() {
  const root = $("adapterList");
  root.innerHTML = `<div class="adapter-item"><span>Loading adapters...</span></div>`;
  try {
    const res = await fetch("/api/adapters");
    const data = await res.json();
    state.adapters = Array.isArray(data.adapters) ? data.adapters : [];
    root.innerHTML = "";
    if (!state.adapters.length) throw new Error("No adapters returned");
    state.adapters.forEach((adapter) => {
      const item = document.createElement("div");
      item.className = "adapter-item clickable-card";
      const metrics = adapter.metrics || {};
      const meta = [adapter.status, metrics.files ? `${metrics.files} files` : null, metrics.python_files ? `${metrics.python_files} py` : null].filter(Boolean).join(" · ");
      item.innerHTML = `<strong>${escapeHtml(adapter.name)}</strong><span>${escapeHtml(meta)} · ${escapeHtml(adapter.summary)}</span>`;
      item.addEventListener("click", () => openAdapterDetail(adapter));
      root.appendChild(item);
    });
    renderSidebarOverview();
  } catch (error) {
    root.innerHTML = `<div class="adapter-item clickable-card"><span>${escapeHtml(error.message)}</span></div>`;
  }
}

async function loadJournal() {
  const root = $("journalList");
  root.innerHTML = `<div class="journal-item"><span>Loading journal...</span></div>`;
  try {
    const res = await fetch(`/api/journal?limit=${encodeURIComponent(state.settings.journalLimit || 50)}`);
    const data = await res.json();
    state.journal = Array.isArray(data.events) ? data.events : [];
    state.journalStats = data.stats || {};
    root.innerHTML = "";
    if (!state.journal.length) {
      root.innerHTML = `<div class="journal-item clickable-card"><span>No events yet.</span></div>`;
      root.firstElementChild?.addEventListener("click", () => openJournalSummaryDetail());
      renderSidebarOverview();
      return;
    }
    state.journal.slice(0, state.settings.journalLimit || 50).forEach((event, index) => {
      const ok = event.ok ?? event.result?.ok;
      const item = document.createElement("div");
      item.className = "journal-item clickable-card";
      const title = event.route || event.type || event.event || `event ${index + 1}`;
      const at = event.recorded_at || event.created_at || event.timestamp || event.time || "";
      item.innerHTML = `
        <button class="journal-main" data-action="details" title="Show journal event details">
          <strong>${escapeHtml(title)} <span class="${ok === false ? "bad-text" : "ok-text"}">${ok === false ? "failed" : "ok"}</span></strong>
          <span>${escapeHtml(event.request || event.goal || event.message || at || JSON.stringify(event).slice(0, 140))}</span>
        </button>
        <div class="journal-actions">
          <button class="ghost-button" data-action="details">Details</button>
          <button class="danger-button" data-action="delete">Delete</button>
        </div>`;
      item.querySelectorAll("[data-action=\"details\"]").forEach((button) => button.addEventListener("click", (clickEvent) => { clickEvent.stopPropagation(); openJournalDetail(event, index); }));
      item.querySelector("[data-action=\"delete\"]").addEventListener("click", (clickEvent) => { clickEvent.stopPropagation(); requestDeleteJournalEntry(event, index); });
      root.appendChild(item);
    });
    renderSidebarOverview();
  } catch (error) {
    root.innerHTML = `<div class="journal-item"><span>${escapeHtml(error.message)}</span></div>`;
  }
}

function requestClearJournal() {
  openConfirmDialog({
    title: "Clear journal?",
    message: "This empties the backend event journal feed. It will not delete your browser sessions, local UI memories, models, or settings.",
    confirmText: "Clear journal",
    onConfirm: clearJournal
  });
}

async function clearJournal() {
  const root = $("journalList");
  root.innerHTML = `<div class="journal-item"><span>Clearing journal...</span></div>`;
  try {
    const res = await fetch("/api/journal/clear", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirm: true })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.error || `Journal clear failed with HTTP ${res.status}`);
    state.journal = [];
    state.journalStats = {};
    root.innerHTML = `<div class="journal-item clickable-card"><strong>Journal cleared</strong><span>${Number.isFinite(data.cleared) ? `${data.cleared} events removed.` : "Event feed is empty now."}</span></div>`;
  } catch (error) {
    root.innerHTML = `<div class="journal-item"><span class="bad-text">${escapeHtml(error.message)}</span></div>`;
  }
}

function requestDeleteJournalEntry(event, index) {
  const title = event.route || event.type || event.event || `event ${index + 1}`;
  openConfirmDialog({
    title: "Delete journal entry?",
    message: `This removes only the selected backend journal event: “${title}”. Browser sessions and memories are untouched.`,
    confirmText: "Delete entry",
    onConfirm: () => deleteJournalEntry(event, index)
  });
}

async function deleteJournalEntry(event, index) {
  const root = $("journalList");
  try {
    const res = await fetch("/api/journal/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirm: true, event, index })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.error || `Journal delete failed with HTTP ${res.status}`);
    await loadJournal();
  } catch (error) {
    root.insertAdjacentHTML("afterbegin", `<div class="journal-item"><span class="bad-text">${escapeHtml(error.message)}</span></div>`);
  }
}

function buildSystemPrompt() {
  const base = $("systemPromptInput").value.trim();
  if (!$("memoryToggle").checked || !state.memories.length) return base || null;
  const memories = state.memories.map((memory, index) => `${index + 1}. ${memory.title ? `${memory.title}: ` : ""}${memory.text}`).join("\n");
  const heading = state.settings.memoryPrefix || DEFAULT_SETTINGS.memoryPrefix;
  return `${base ? `${base}\n\n` : ""}${heading}:\n${memories}`;
}

function buildModelOptions() {
  const opts = state.settings.modelOptions || {};
  const out = {};
  const numericKeys = ["temperature", "num_ctx", "top_p", "top_k", "repeat_penalty", "seed", "num_predict"];
  numericKeys.forEach((key) => {
    const value = Number(opts[key]);
    if (!Number.isFinite(value)) return;
    if ((key === "seed" || key === "num_predict") && value < 0) return;
    out[key] = value;
  });
  if (Array.isArray(opts.stop) && opts.stop.length) out.stop = opts.stop.filter(Boolean);
  if (opts.keep_alive) out.keep_alive = String(opts.keep_alive);
  if (state.settings.enableThinking !== false) out.enable_thinking = true;
  return out;
}

function buildResponseFormat() {
  return state.settings.responseFormat === "json" ? "json" : null;
}

function previewAutoRoute(text) {
  if ($("modelSelect").value) return;
  const profile = routeModelForText(text);
  if (!profile) return;
  $("requestStats").textContent = `auto → ${profile.category}`;
}

async function sendMessage() {
  if (state.busy) return;
  const input = $("promptInput");
  const text = input.value.trim();
  if (!text) return;
  state.busy = true;
  const started = performance.now();
  input.value = "";
  const modelOptions = buildModelOptions();
  const userMessage = addSessionMessage("user", text, { model: $("modelSelect").value || "auto" });
  chatLog.querySelector(".empty-state")?.remove();
  renderMessage(userMessage);
  const assistantMessage = addSessionMessage("assistant", "", { thinking: "", toolCalls: [], model: $("modelSelect").value || "auto", options: modelOptions });
  const assistantNode = renderMessage(assistantMessage);
  scrollChat();
  const contentNode = assistantNode.querySelector(".message-content");
  const payload = {
    text,
    confirm: $("confirmToggle").checked,
    stream: $("streamToggle").checked,
    model: $("modelSelect").value || null,
    system_prompt: buildSystemPrompt(),
    options: modelOptions,
    response_format: buildResponseFormat()
  };
  $("requestStats").textContent = "running...";
  $("sendBtn").textContent = "X";
  $("sendBtn").title = "Stop";

  const controller = new AbortController();
  state.lastController = controller;
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    if (payload.stream && res.headers.get("content-type")?.includes("ndjson")) {
      await readNdjsonStream(res, (chunk) => {
        if (chunk.type === "content_delta") {
          assistantMessage.content += chunk.delta || "";
          contentNode.textContent = assistantMessage.content;
        } else if (chunk.type === "thinking_delta") {
          assistantMessage.thinking += chunk.delta || "";
          renderActivityBox(assistantNode, assistantMessage);
        } else if (chunk.type === "tool_calls") {
          assistantMessage.toolCalls = chunk.tool_calls || [];
          renderActivityBox(assistantNode, assistantMessage);
        } else if (chunk.type === "final") {
          assistantMessage.ok = Boolean(chunk.ok);
          assistantMessage.toolCalls = chunk.tool_calls || [];
          assistantMessage.model = chunk.data?.model || assistantMessage.model;
          assistantMessage.modelRoute = chunk.data?.model_route || null;
          if (!assistantMessage.content.trim()) assistantMessage.content = stripThinkTags(chunk.message || "");
          if (!assistantMessage.thinking.trim()) assistantMessage.thinking = chunk.thinking || extractThinkText(chunk.message || "");
          contentNode.textContent = assistantMessage.content;
          renderActivityBox(assistantNode, assistantMessage);
        }
        scrollChat();
      });
    } else {
      const data = await res.json();
      assistantMessage.ok = Boolean(data.ok);
      assistantMessage.content = stripThinkTags(data.message || "");
      assistantMessage.thinking = data.thinking || extractThinkText(data.message || "");
      assistantMessage.toolCalls = data.tool_calls || [];
      assistantMessage.model = data.data?.model || assistantMessage.model;
      assistantMessage.modelRoute = data.data?.model_route || null;
      contentNode.textContent = assistantMessage.content;
      renderActivityBox(assistantNode, assistantMessage);
    }
  } catch (error) {
    assistantMessage.ok = false;
    assistantMessage.content = error.name === "AbortError" ? "Request stopped." : `Request failed: ${error.message}`;
    contentNode.textContent = assistantMessage.content;
  } finally {
    assistantMessage.latencyMs = Math.round(performance.now() - started);
    const sessionMessage = activeSession().messages.find((msg) => msg.id === assistantMessage.id);
    Object.assign(sessionMessage, assistantMessage);
    persist();
    state.busy = false;
    state.lastController = null;
    $("sendBtn").textContent = ">";
    $("sendBtn").title = "Send";
    $("requestStats").textContent = `${assistantMessage.latencyMs} ms · ${assistantMessage.content.length} chars`;
    await loadJournal();
    scrollChat();
  }
}

async function readNdjsonStream(response, onChunk) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try { onChunk(JSON.parse(trimmed)); } catch (error) { console.warn("Bad NDJSON chunk", trimmed, error); }
    }
  }
  if (buffer.trim()) {
    try { onChunk(JSON.parse(buffer.trim())); } catch (error) { console.warn("Bad final NDJSON chunk", buffer, error); }
  }
}

async function runAutonomous() {
  const goal = $("promptInput").value.trim();
  if (!goal) return;
  state.busy = true;
  addSessionMessage("user", `Autonomous run: ${goal}`);
  const toolMessage = addSessionMessage("tool", "Running autonomous plan...", { toolCalls: [] });
  renderChat();
  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal, max_steps: 5, confirm: $("confirmToggle").checked, stream: false, model: $("modelSelect").value || null, options: buildModelOptions() })
    });
    const data = await res.json();
    toolMessage.ok = Boolean(data.ok);
    toolMessage.content = data.message || "Done.";
    toolMessage.toolCalls = data.tool_calls || [];
  } catch (error) {
    toolMessage.ok = false;
    toolMessage.content = `Autonomous run failed: ${error.message}`;
  } finally {
    Object.assign(activeSession().messages.find((msg) => msg.id === toolMessage.id), toolMessage);
    state.busy = false;
    persist();
    renderChat();
    await loadJournal();
  }
}

async function runManualTool() {
  closeMobileDrawers();
  const tool = $("toolSelect").value;
  const root = $("toolResult");
  root.innerHTML = `<span>Running ${escapeHtml(tool)}...</span>`;
  let args;
  try { args = JSON.parse($("toolArgs").value || "{}"); }
  catch (error) {
    root.innerHTML = `<span class="bad-text">Invalid JSON: ${escapeHtml(error.message)}</span>`;
    return;
  }

  let result;
  try {
    const res = await fetch("/api/tool", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tool, arguments: args, confirm: $("toolConfirmToggle").checked })
    });
    if (res.status === 404) throw new Error("manual endpoint missing");
    result = await res.json();
  } catch {
    result = await runManualToolFallback(tool, args);
  }

  const call = result.tool_call || result;
  root.innerHTML = `<pre>${escapeHtml(JSON.stringify(call, null, 2))}</pre>`;
  root.onclick = () => openToolCallDetail(call);
  addSessionMessage("tool", `${tool}: ${call.ok ? "ok" : "failed"}`, { toolCalls: [call] });
  renderChat();
  await loadJournal();
}

async function runManualToolFallback(tool, args) {
  const text = fallbackPromptForTool(tool, args);
  const res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, confirm: $("toolConfirmToggle").checked, stream: false })
  });
  const data = await res.json();
  return { tool_call: { tool_name: tool, ok: Boolean(data.ok), summary: data.message || "Fallback /api/ask completed.", data: { fallback: true, sent_text: text, tool_calls: data.tool_calls || [] } } };
}

function fallbackPromptForTool(tool, args) {
  const q = args.query || args.path || args.path_text || args.command || args.goal || "";
  const map = {
    file_search: `find file ${q}`,
    read_file: `read file ${args.path_text || args.path || q}`,
    content_search: `search content ${q}`,
    build_index: "build index",
    query_index: `query index ${q}`,
    web_search: `search web for ${q}`,
    shell_command: `run ${args.command || q}`,
    adapter_inventory: "show adapters",
    tree_view: "show project structure",
    library_info: "library info",
    library_search: `library search ${q}`
  };
  return map[tool] || `Run tool ${tool} with arguments ${JSON.stringify(args)}`;
}

function syncSettingsFromMainControls() {
  state.settings.stream = $("streamToggle")?.checked ?? state.settings.stream;
  state.settings.confirm = $("confirmToggle")?.checked ?? state.settings.confirm;
  state.settings.attachMemories = $("memoryToggle")?.checked ?? state.settings.attachMemories;
  state.settings.autoScroll = $("autoScrollToggle")?.checked ?? state.settings.autoScroll;
  state.settings.density = document.documentElement.dataset.density || state.settings.density;
}

function applySettingsToMainControls() {
  document.documentElement.dataset.density = state.settings.density || "comfortable";
  $("streamToggle").checked = Boolean(state.settings.stream);
  $("confirmToggle").checked = Boolean(state.settings.confirm);
  $("memoryToggle").checked = Boolean(state.settings.attachMemories);
  $("autoScrollToggle").checked = Boolean(state.settings.autoScroll);
  applySettingsVisuals();
}

function applySettingsVisuals() {
  document.documentElement.dataset.density = state.settings.density || "comfortable";
  document.documentElement.dataset.compactTools = state.settings.compactTools ? "true" : "false";
  document.documentElement.style.setProperty("--message-max", `${Number(state.settings.messageWidth) || 78}ch`);
}

function syncSettingsModal() {
  populateSettingsModelSelect();
  $("settingsModelSelect").value = $("modelSelect").value || "";
  $("settingsDensitySelect").value = state.settings.density || "comfortable";
  $("settingsStreamToggle").checked = Boolean(state.settings.stream);
  $("settingsConfirmToggle").checked = Boolean(state.settings.confirm);
  $("settingsMemoryToggle").checked = Boolean(state.settings.attachMemories);
  $("settingsAutoScrollToggle").checked = Boolean(state.settings.autoScroll);
  $("settingsOpenThinkingToggle").checked = Boolean(state.settings.openThinking);
  $("settingsDetailsToggle").checked = Boolean(state.settings.detailsEnabled);
  $("settingsCompactToolsToggle").checked = Boolean(state.settings.compactTools);
  $("settingsJournalLimit").value = state.settings.journalLimit || 50;
  $("settingsMessageWidth").value = state.settings.messageWidth || 78;
  $("settingsMemoryPrefix").value = state.settings.memoryPrefix || DEFAULT_SETTINGS.memoryPrefix;
  $("settingsResponseFormat").value = state.settings.responseFormat || "";
  const opts = state.settings.modelOptions || {};
  $("settingsTemperature").value = opts.temperature ?? 0.2;
  $("settingsNumCtx").value = opts.num_ctx ?? 4096;
  $("settingsTopP").value = opts.top_p ?? 0.95;
  $("settingsTopK").value = opts.top_k ?? 40;
  $("settingsRepeatPenalty").value = opts.repeat_penalty ?? 1.1;
  $("settingsSeed").value = opts.seed ?? -1;
  $("settingsNumPredict").value = opts.num_predict ?? -1;
  $("settingsKeepAlive").value = opts.keep_alive ?? "";
  $("settingsStopSequences").value = Array.isArray(opts.stop) ? opts.stop.join("\n") : "";
  $("settingsSystemPromptInput").value = $("systemPromptInput").value;
  renderSettingsMemoryStats();
}

function renderSettingsMemoryStats() {
  const root = $("settingsMemoryStats");
  const chars = state.memories.reduce((sum, memory) => sum + String(memory.text || "").length, 0);
  root.innerHTML = `
    <div><strong>${state.memories.length}</strong><span>memories</span></div>
    <div><strong>${state.memories.filter((m) => m.pinned).length}</strong><span>pinned</span></div>
    <div><strong>${chars}</strong><span>chars injected when enabled</span></div>`;
}

function openSettings() {
  syncSettingsModal();
  $("settingsModal").hidden = false;
  $("settingsModelSelect").focus();
}

function closeSettings() {
  $("settingsModal").hidden = true;
}

function saveSettings() {
  $("modelSelect").value = $("settingsModelSelect").value;
  state.settings.density = $("settingsDensitySelect").value;
  state.settings.stream = $("settingsStreamToggle").checked;
  state.settings.confirm = $("settingsConfirmToggle").checked;
  state.settings.attachMemories = $("settingsMemoryToggle").checked;
  state.settings.autoScroll = $("settingsAutoScrollToggle").checked;
  state.settings.openThinking = $("settingsOpenThinkingToggle").checked;
  state.settings.detailsEnabled = $("settingsDetailsToggle").checked;
  state.settings.compactTools = $("settingsCompactToolsToggle").checked;
  state.settings.journalLimit = Math.max(5, Number($("settingsJournalLimit").value) || 50);
  state.settings.messageWidth = Math.max(52, Math.min(120, Number($("settingsMessageWidth").value) || 78));
  state.settings.memoryPrefix = $("settingsMemoryPrefix").value.trim() || DEFAULT_SETTINGS.memoryPrefix;
  state.settings.responseFormat = $("settingsResponseFormat").value;
  state.settings.modelOptions = {
    temperature: Number($("settingsTemperature").value),
    num_ctx: Number($("settingsNumCtx").value),
    top_p: Number($("settingsTopP").value),
    top_k: Number($("settingsTopK").value),
    repeat_penalty: Number($("settingsRepeatPenalty").value),
    seed: Number($("settingsSeed").value),
    num_predict: Number($("settingsNumPredict").value),
    keep_alive: $("settingsKeepAlive").value.trim(),
    stop: $("settingsStopSequences").value.split("\n").map((line) => line.trim()).filter(Boolean)
  };
  $("systemPromptInput").value = $("settingsSystemPromptInput").value;
  applySettingsToMainControls();
  updateModelMeta();
  persist();
  renderChat();
  closeSettings();
  loadJournal();
}

function switchSettingsTab(tabName) {
  document.querySelectorAll(".settings-tab").forEach((button) => button.classList.toggle("active", button.dataset.settingsTab === tabName));
  document.querySelectorAll(".settings-tab-panel").forEach((panel) => panel.classList.toggle("active", panel.dataset.settingsPanel === tabName));
}

function openConfirmDialog({ title, message, confirmText = "Confirm", onConfirm }) {
  state.pendingConfirm = onConfirm;
  $("confirmTitle").textContent = title;
  $("confirmMessage").textContent = message;
  $("confirmActionBtn").textContent = confirmText;
  $("confirmDialog").hidden = false;
  $("confirmCancelBtn").focus();
}

function closeConfirmDialog() {
  state.pendingConfirm = null;
  $("confirmDialog").hidden = true;
}

async function acceptConfirmDialog() {
  const action = state.pendingConfirm;
  closeConfirmDialog();
  if (typeof action === "function") await action();
}

function detailTable(rows) {
  return `<dl class="detail-table">${rows.filter((row) => row[1] !== undefined && row[1] !== null && row[1] !== "").map(([key, value]) => `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></div>`).join("")}</dl>`;
}

function jsonBlock(value) {
  return `<pre class="detail-json">${escapeHtml(JSON.stringify(value, null, 2))}</pre>`;
}

function openDetailModal({ eyebrow = "Details", title = "Details", html = "", payload = null }) {
  state.detailPayload = payload;
  $("detailEyebrow").textContent = eyebrow;
  $("detailTitle").textContent = title;
  $("detailBody").innerHTML = html || jsonBlock(payload || {});
  $("detailModal").hidden = false;
  $("detailCloseBtn").focus();
}

function closeDetailModal() {
  $("detailModal").hidden = true;
  state.detailPayload = null;
}

function openMessageDetail(message) {
  const stats = [
    ["Role", message.role],
    ["Created", new Date(message.createdAt).toLocaleString()],
    ["Status", message.ok === false ? "failed" : "ok"],
    ["Model", message.model || "not recorded"],
    ["Route", message.modelRoute?.category || "not recorded"],
    ["Route reason", message.modelRoute?.reason || ""],
    ["Latency", message.latencyMs ? `${message.latencyMs} ms` : "not recorded"],
    ["Characters", String(message.content || "").length],
    ["Words", wordCount(message.content)],
    ["Approx tokens", roughTokens(message.content)],
    ["Thinking chars", String(message.thinking || "").length],
    ["Tool calls", (message.toolCalls || []).length]
  ];
  openDetailModal({
    eyebrow: "Message",
    title: message.role === "user" ? "User message" : message.role === "tool" ? "Tool message" : "Assistant message",
    html: `${detailTable(stats)}<h3>Content</h3><pre class="detail-json">${escapeHtml(message.content || "")}</pre>${message.thinking ? `<h3>Thinking</h3><pre class="detail-json">${escapeHtml(message.thinking)}</pre>` : ""}<h3>Raw</h3>${jsonBlock(message)}`,
    payload: message
  });
}

function openSessionDetail(session) {
  if (!session) return;
  const messages = session.messages || [];
  const toolCalls = messages.reduce((sum, msg) => sum + (msg.toolCalls || []).length, 0);
  openDetailModal({
    eyebrow: "Session",
    title: session.title || "Session",
    html: `${detailTable([
      ["Created", new Date(session.createdAt).toLocaleString()],
      ["Messages", messages.length],
      ["User messages", messages.filter((m) => m.role === "user").length],
      ["Assistant messages", messages.filter((m) => m.role === "assistant").length],
      ["Tool calls", toolCalls],
      ["Characters", messages.reduce((sum, msg) => sum + String(msg.content || "").length, 0)]
    ])}<h3>Raw</h3>${jsonBlock(session)}`,
    payload: session
  });
}

function openMemoryDetail(memory) {
  openDetailModal({
    eyebrow: "Memory",
    title: memory.title || "Memory",
    html: `${detailTable([
      ["Pinned", memory.pinned ? "yes" : "no"],
      ["Created", memory.createdAt ? new Date(memory.createdAt).toLocaleString() : "unknown"],
      ["Characters", String(memory.text || "").length],
      ["Approx tokens", roughTokens(memory.text)]
    ])}<h3>Memory text</h3><pre class="detail-json">${escapeHtml(memory.text || "")}</pre><h3>Raw</h3>${jsonBlock(memory)}`,
    payload: memory
  });
}

function openModelDetail(modelName) {
  const profile = MODEL_PROFILES.find((item) => item.model === modelName) || null;
  const live = state.models.find((item) => item.name === modelName || item.model === modelName) || null;
  const payload = { selected: modelName || "auto", profile, live, model_options: buildModelOptions(), response_format: buildResponseFormat() };
  openDetailModal({
    eyebrow: "Model",
    title: modelName || "Auto route",
    html: `${detailTable([
      ["Selected", modelName || "Auto route"],
      ["Profile", profile?.category || "server-side / live"],
      ["Job", profile?.job || "not mapped"],
      ["Live size", live?.size ? prettyBytes(live.size) : "not found in /api/models"],
      ["Modified", live?.modified_at || "unknown"],
      ["Response format", state.settings.responseFormat || "text"]
    ])}<h3>Options sent with chat</h3>${jsonBlock(buildModelOptions())}<h3>Raw</h3>${jsonBlock(payload)}`,
    payload
  });
}

function openToolDetail(id) {
  const doc = { id, ...(TOOL_DOCS[id] || {}), ...toolCardFor(id), example: TOOL_EXAMPLES[id] ?? {} };
  const calls = activeSession()?.messages?.flatMap((msg) => msg.toolCalls || []).filter((call) => (call.tool_name || call.name) === id) || [];
  openDetailModal({
    eyebrow: "Tool",
    title: id,
    html: `${detailTable([
      ["Name", doc.name || id],
      ["Safety", doc.safety || "ready"],
      ["Available", state.tools.includes(id) ? "yes" : "from fallback docs"],
      ["Calls in active session", calls.length],
      ["Summary", doc.summary || "No summary available"],
      ["Usage", doc.usage || doc.guidance || "Use from the manual tool selector."]
    ])}<h3>Example arguments</h3>${jsonBlock(doc.example || {})}<h3>Raw</h3>${jsonBlock(doc)}`,
    payload: doc
  });
}

function openToolCallDetail(call) {
  openDetailModal({
    eyebrow: "Tool call",
    title: call.tool_name || call.name || "Tool call",
    html: `${detailTable([
      ["Tool", call.tool_name || call.name || "unknown"],
      ["Status", call.ok ? "ok" : "failed"],
      ["Summary chars", String(call.summary || "").length]
    ])}<h3>Summary</h3><pre class="detail-json">${escapeHtml(call.summary || "")}</pre><h3>Raw</h3>${jsonBlock(call)}`,
    payload: call
  });
}

function openAdapterDetail(adapter) {
  const metrics = adapter.metrics || {};
  const localMentions = state.sessions.reduce((count, session) => count + (session.messages || []).filter((msg) => JSON.stringify(msg).toLowerCase().includes(String(adapter.name || adapter.adapter_id || "").toLowerCase())).length, 0);
  const usage = adapter.usage || [];
  openDetailModal({
    eyebrow: "Adapter",
    title: adapter.name || adapter.adapter_id || "Adapter",
    html: `${detailTable([
      ["ID", adapter.adapter_id || adapter.id],
      ["Status", adapter.status],
      ["Summary", adapter.summary],
      ["Path", adapter.details?.path || metrics.path],
      ["Files", metrics.files],
      ["Python files", metrics.python_files],
      ["Markdown files", metrics.markdown_files],
      ["JSON files", metrics.json_files],
      ["Total size", metrics.total_bytes ? prettyBytes(metrics.total_bytes) : "unknown"],
      ["Modified", metrics.modified_at],
      ["Created/status changed", metrics.created_or_changed_at],
      ["Browser messages mentioning it", localMentions],
      ["Journal mentions", adapter.journal_mentions]
    ])}${usage.length ? `<h3>Usage ideas</h3><ul class="detail-list">${usage.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}<h3>Details</h3>${jsonBlock(adapter.details || {})}<h3>Raw</h3>${jsonBlock(adapter)}`,
    payload: adapter
  });
}

function openJournalDetail(event, index) {
  openDetailModal({
    eyebrow: "Journal event",
    title: event.route || event.type || `Event ${index + 1}`,
    html: `${detailTable([
      ["Index", index + 1],
      ["Route/type", event.route || event.type || event.event],
      ["Status", (event.ok ?? event.result?.ok) === false ? "failed" : "ok"],
      ["Created", event.created_at || event.timestamp || event.time || "unknown"],
      ["Request", event.request || event.goal || event.message]
    ])}<h3>Raw event</h3>${jsonBlock(event)}`,
    payload: event
  });
}

function openJournalSummaryDetail() {
  openDetailModal({
    eyebrow: "Journal",
    title: "Journal feed",
    html: `${detailTable([
      ["Loaded events", state.journal.length],
      ["Configured display limit", state.settings.journalLimit],
      ["Backend total", state.journalStats.total_events],
      ["Journal path", state.journalStats.path]
    ])}<h3>Stats</h3>${jsonBlock(state.journalStats)}`,
    payload: { events: state.journal, stats: state.journalStats }
  });
}

function openCollectionDetail(title, copy, payload) {
  openDetailModal({ eyebrow: "Panel", title, html: `<p class="modal-copy">${escapeHtml(copy)}</p>${jsonBlock(payload)}`, payload });
}

function bindModalChrome() {
  $("settingsBtn").addEventListener("click", openSettings);
  $("closeSettingsBtn").addEventListener("click", closeSettings);
  $("cancelSettingsBtn").addEventListener("click", closeSettings);
  $("saveSettingsBtn").addEventListener("click", saveSettings);
  document.querySelectorAll(".settings-tab").forEach((button) => button.addEventListener("click", () => switchSettingsTab(button.dataset.settingsTab)));
  $("settingsClearJournalBtn").addEventListener("click", () => { closeSettings(); requestClearJournal(); });
  $("settingsDeleteAllSessionsBtn")?.addEventListener("click", () => { closeSettings(); requestDeleteAllSessions(); });
  $("settingsExportAllBtn").addEventListener("click", exportAllSessions);
  $("settingsClearBrowserBtn").addEventListener("click", () => {
    closeSettings();
    openConfirmDialog({
      title: "Clear browser UI state?",
      message: "This deletes local browser sessions, memories, and settings for this UI. Backend files and journal are untouched.",
      confirmText: "Clear browser state",
      onConfirm: clearBrowserState
    });
  });
  $("confirmCancelBtn").addEventListener("click", closeConfirmDialog);
  $("confirmActionBtn").addEventListener("click", acceptConfirmDialog);
  $("confirmDialog").addEventListener("click", (event) => { if (event.target.id === "confirmDialog") closeConfirmDialog(); });
  $("settingsModal").addEventListener("click", (event) => { if (event.target.id === "settingsModal") closeSettings(); });
  $("closeDetailBtn").addEventListener("click", closeDetailModal);
  $("detailCloseBtn").addEventListener("click", closeDetailModal);
  $("detailModal").addEventListener("click", (event) => { if (event.target.id === "detailModal") closeDetailModal(); });
  $("detailCopyBtn").addEventListener("click", async () => {
    await navigator.clipboard.writeText(JSON.stringify(state.detailPayload || {}, null, 2));
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    if (!$("confirmDialog").hidden) closeConfirmDialog();
    else if (!$("detailModal").hidden) closeDetailModal();
    else if (!$("settingsModal").hidden) closeSettings();
    else closeMobileDrawers();
  });
}

function exportSession() {
  const session = activeSession();
  downloadJson(`${(session.title || "session").replace(/[^a-z0-9]+/gi, "-").toLowerCase()}.json`, session);
}

function exportAllSessions() {
  downloadJson("showcase-ui-sessions.json", { exportedAt: new Date().toISOString(), sessions: state.sessions, memories: state.memories, settings: state.settings });
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function clearActiveSession() {
  const session = activeSession();
  if (!session) return;
  session.messages = [];
  session.title = "New session";
  persist();
  renderAll();
}

function clearBrowserState() {
  Object.values(STORAGE_KEYS).forEach((key) => localStorage.removeItem(key));
  state.sessions = [];
  state.memories = [];
  state.settings = structuredClone(DEFAULT_SETTINGS);
  createSession(false);
  applySettingsToMainControls();
  persist();
  renderAll();
}

function addMemory() {
  const text = prompt("Memory text to attach to future requests:");
  if (!text?.trim()) return;
  const title = prompt("Optional short title:") || "Memory";
  state.memories.unshift({ id: uid("memory"), title: title.trim(), text: text.trim(), pinned: false, createdAt: new Date().toISOString() });
  persist();
  renderMemories();
}

function bindPanelDetails() {
  $("brandCard").addEventListener("click", () => openCollectionDetail("Local Showcase", "A local-first tool-aware Ollama cockpit with chat, tools, adapters, journal, model settings, and browser-side memories.", { version: "ui-v4-mobile", models: state.models.length, tools: state.tools.length, adapters: state.adapters.length }));
  $("modelPanel").addEventListener("dblclick", () => openModelDetail($("modelSelect").value));
  $("sessionsPanel").addEventListener("dblclick", () => openSessionDetail(activeSession()));
  $("memoriesPanel").addEventListener("dblclick", () => openCollectionDetail("Memories", `${state.memories.length} local browser memories.`, state.memories));
  $("sessionHeader").addEventListener("dblclick", () => openSessionDetail(activeSession()));
  $("toolsPanel").addEventListener("dblclick", () => openCollectionDetail("Tools", `${state.tools.length} available tools.`, { tools: state.tools, tool_cards: state.toolCards }));
  $("adaptersPanel").addEventListener("dblclick", () => openCollectionDetail("Adapters", `${state.adapters.length} workspace adapters loaded.`, state.adapters));
  $("journalPanel").addEventListener("dblclick", openJournalSummaryDetail);
  $("composerPanel").addEventListener("dblclick", () => openCollectionDetail("Composer", "Prompt composer details and current request options.", { model: $("modelSelect").value || "auto", options: buildModelOptions(), system_prompt_chars: $("systemPromptInput").value.length }));
}


function setMobilePanel(panel){
  document.body.classList.toggle("mobile-left-open",panel==="left");
  document.body.classList.toggle("mobile-right-open",panel==="right");
  const scrim=$("mobileScrim");
  if(scrim) scrim.hidden=panel!=="left"&&panel!=="right";
  document.querySelectorAll(".mobile-nav-button[data-mobile-panel]").forEach((button)=>{
    button.classList.toggle("active",button.dataset.mobilePanel===panel||(panel==="chat"&&button.dataset.mobilePanel==="chat"));
  });
}
function closeMobileDrawers(){setMobilePanel("chat");}
function bindMobileShell(){
  document.querySelectorAll(".mobile-nav-button[data-mobile-panel]").forEach((button)=>{button.addEventListener("click",()=>setMobilePanel(button.dataset.mobilePanel));});
  document.querySelectorAll("[data-mobile-close]").forEach((button)=>{button.addEventListener("click",closeMobileDrawers);});
  $("mobileScrim")?.addEventListener("click",closeMobileDrawers);
  document.querySelector('[data-mobile-action="settings"]')?.addEventListener("click",()=>{closeMobileDrawers();openSettings();});
  window.matchMedia("(min-width: 761px)").addEventListener("change",(event)=>{if(event.matches) closeMobileDrawers();});
}

function bindPageShell() {
  document.querySelectorAll("[data-page-target]").forEach((button) => {
    button.addEventListener("click", () => setActivePage(button.dataset.pageTarget));
  });
  $("sidebarToggleBtn")?.addEventListener("click", () => setMobilePanel("left"));
}

function bindEvents() {
  $("sendBtn").addEventListener("click", () => {
    if (state.busy && state.lastController) state.lastController.abort();
    else { closeMobileDrawers(); sendMessage(); }
  });
  $("promptInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });
  $("promptInput").addEventListener("input", (event) => previewAutoRoute(event.target.value));
  chatLog.addEventListener("click", (event) => {
    const starter = event.target.closest("[data-preset]");
    if (!starter) return;
    event.preventDefault();
    event.stopPropagation();
    applyStarterPrompt(starter.dataset.preset);
  });
  $("modelSelect").addEventListener("change", () => { updateModelMeta(); persist(); });
  $("toolSelect").addEventListener("change", updateToolExample);
  $("runToolBtn").addEventListener("click", runManualTool);
  $("runAutonomousBtn").addEventListener("click", runAutonomous);
  $("newSessionBtn").addEventListener("click", () => createSession(true));
  $("addMemoryBtn").addEventListener("click", addMemory);
  $("exportBtn").addEventListener("click", exportSession);
  $("clearBtn").addEventListener("click", clearActiveSession);
  $("refreshAdaptersBtn").addEventListener("click", loadAdapters);
  $("refreshJournalBtn").addEventListener("click", loadJournal);
  $("clearJournalBtn").addEventListener("click", requestClearJournal);
  $("systemPromptBtn").addEventListener("click", () => {
    const box = $("systemPromptInput");
    box.hidden = !box.hidden;
    if (!box.hidden) box.focus();
  });
  $("densityBtn").addEventListener("click", () => {
    state.settings.density = state.settings.density === "compact" ? "comfortable" : "compact";
    applySettingsToMainControls();
    persist();
  });
  ["confirmToggle", "memoryToggle", "autoScrollToggle", "streamToggle", "systemPromptInput"].forEach((id) => {
    $(id).addEventListener("change", persist);
    $(id).addEventListener("input", persist);
  });
  bindModalChrome();
  bindPanelDetails();
  bindMobileShell();
  bindPageShell();
  bindDragDrop();
}

function appendPrompt(text) {
  const input = $("promptInput");
  input.value = `${input.value}${input.value ? "\n" : ""}${text}`;
  input.focus();
}

function applyStarterPrompt(kind) {
  const prompts = {
    code: "Review this code/system design and point out exact fixes:\n",
    linux: "Diagnose this Linux/system issue step by step:\n",
    research: "Analyze this carefully, compare tradeoffs, and give an implementation path:\n",
    structure: "Look around this project and summarize its structure before answering:\n"
  };
  appendPrompt(prompts[kind] || "");
}

function bindDragDrop() {
  const composer = document.querySelector(".composer");
  const dropZone = $("dropZone");
  ["dragenter", "dragover"].forEach((eventName) => composer.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.hidden = false;
  }));
  ["dragleave", "drop"].forEach((eventName) => composer.addEventListener(eventName, (event) => {
    event.preventDefault();
    if (eventName === "drop") {
      const text = event.dataTransfer.getData("text/plain");
      if (text) appendPrompt(text);
    }
    dropZone.hidden = true;
  }));
}

async function boot() {
  loadLocalState();
  bindEvents();
  renderAll();
  await Promise.allSettled([loadModels(), loadTools(), loadAdapters(), loadJournal()]);
  renderAll();
}

boot();
