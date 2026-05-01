const TOOL_EXAMPLES = {
  adapter_inventory: {},
  build_index: {},
  content_search: { query: "ToolRuntime" },
  create_memory: { key: "style", value: "prefers concise answers" },
  delete_memory: { key: "style" },
  draft_system_prompt: { title: "Coding assistant", goal: "direct implementation help", context: "" },
  edit_memory: { key: "style", value: "prefers detailed but direct answers" },
  file_search: { query: "README" },
  library_info: {},
  library_read_epub: { id: "", query: "", max_chars: 12000 },
  library_read_zim: { id: "", title: "" },
  library_search: { query: "local models", limit: 10 },
  query_index: { query: "routing and tool catalog" },
  read_file: { path: "README.md" },
  list_memories: {},
  load_memory: { key: "style" },
  save_memory: { key: "style", value: "prefers concise answers" },
  shell_command: { command: "git status" },
  tree_view: { path: ".", max_depth: 4 },
  web_search: { query: "Ollama structured outputs" }
};

const TOOL_DOCS = {
  adapter_inventory: { name: "Adapter Inventory", safety: "read-only", summary: "Show which workspace adapters are detected and usable.", usage: "Use this when you want provenance, workspace status, or adapter summaries." },
  build_index: { name: "Build Index", safety: "read/write state", summary: "Build the lightweight local index from text files.", usage: "Run after a big repo change or before repeated codebase questions." },
  content_search: { name: "Content Search", safety: "read-only", summary: "Search file contents for a string or symbol.", usage: "Useful for locating functions, prompts, routes, or feature flags." },
  create_memory: { name: "Create Memory", safety: "local state", summary: "Store a user preference or stable fact by key.", usage: "Use only when the user explicitly asks the assistant to remember something." },
  delete_memory: { name: "Delete Memory", safety: "local state", summary: "Forget a stored user memory by key.", usage: "Use when the user asks to forget or remove a remembered detail." },
  draft_system_prompt: { name: "Draft System Prompt", safety: "read-only suggestion", summary: "Draft a structured system prompt for user review.", usage: "Use from settings guided creation or when the user asks to create reusable behavior." },
  edit_memory: { name: "Edit Memory", safety: "local state", summary: "Replace a stored user memory value.", usage: "Use when the user corrects or changes a remembered detail." },
  file_search: { name: "File Search", safety: "read-only", summary: "Find files by filename.", usage: "Use before read_file when you know part of a filename but not the exact path." },
  library_info: { name: "Library Info", safety: "read-only", summary: "Show configured local library sources.", usage: "Use to confirm EPUB/ZIM library availability." },
  library_read_epub: { name: "Read EPUB", safety: "read-only", summary: "Read a selected EPUB item or matching passage.", usage: "Requires a library item id from library_search." },
  library_read_zim: { name: "Read ZIM", safety: "read-only", summary: "Read a local ZIM article by id/title.", usage: "Useful for offline docs or knowledge bases." },
  library_search: { name: "Library Search", safety: "read-only", summary: "Search the local library catalog.", usage: "Use before reading EPUB/ZIM content." },
  query_index: { name: "Query Index", safety: "read-only", summary: "Search the built local index.", usage: "Best for repo-level questions after build_index has run." },
  read_file: { name: "Read File", safety: "read-only", summary: "Read a local text file.", usage: "Use with an exact path from file_search or tree_view." },
  list_memories: { name: "List Memories", safety: "local state", summary: "Show stored memory keys and values.", usage: "Use before loading, editing, or deleting a memory when the key is unknown." },
  load_memory: { name: "Load Memory", safety: "local state", summary: "Read one stored memory by key.", usage: "Use when a known preference or personal detail is relevant." },
  save_memory: { name: "Save Memory", safety: "local state", summary: "Store a user preference or stable fact by key.", usage: "Use only for explicit remember/store requests." },
  shell_command: { name: "Shell Command", safety: "guarded", summary: "Run a shell command with blocked and confirm-required patterns.", usage: "Use only for explicit terminal tasks like git status, tests, or safe inspection." },
  tree_view: { name: "Tree View", safety: "read-only", summary: "Show a shallow project tree.", usage: "Good for quickly understanding project layout." },
  web_search: { name: "Web Search", safety: "network", summary: "Run a simple web lookup.", usage: "Use for docs, current info, or external references." }
};

const PLANNER_SAFE_TOOLS = new Set([
  "adapter_inventory",
  "build_index",
  "content_search",
  "create_memory",
  "delete_memory",
  "draft_system_prompt",
  "edit_memory",
  "expand_search_result",
  "file_search",
  "library_info",
  "library_read_epub",
  "library_read_zim",
  "library_search",
  "query_index",
  "read_file",
  "list_memories",
  "load_memory",
  "save_memory",
  "tree_view",
  "web_search"
]);

const TOOL_PRESETS = [
  { id: "inspect_repo", label: "Inspect repo", tool: "tree_view", args: { path: ".", max_depth: 4 } },
  { id: "read_readme", label: "Read README", tool: "read_file", args: { path: "README.md" } },
  { id: "build_index", label: "Build index", tool: "build_index", args: {} },
  { id: "query_index", label: "Query index", tool: "query_index", args: { query: "routing and tool catalog" } },
  { id: "git_status", label: "Git status", tool: "git_status", args: {} },
  { id: "search_web", label: "Search web", tool: "web_search", args: { query: "Ollama structured outputs" } },
  { id: "search_files", label: "Search files", tool: "file_search", args: { query: "README" } }
];

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
  sidebarCollapsed: false,
  journalLimit: 50,
  messageWidth: 78,
  memoryPrefix: "Relevant local UI memories",
  profilePrefix: "Relevant profile information",
  responseFormat: "",
  runtimeTimeouts: {
    ollama: 120,
    tools: 30
  },
  theme: {
    primary: "#07100d",
    accent: "#78f0ad",
    accentTwo: "#b6ffd2",
    panel: "#13261e",
    text: "#edf7f1",
    font: "system"
  },
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

const DEFAULT_PROFILE = {
  name: "",
  nickname: "",
  about: "",
  preferences: "",
  other: "",
  userAvatar: "",
  assistantAvatar: ""
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
  overview: {
    eyebrow: "Overview",
    title: "Runtime overview",
    summary: "Inspect the local runtime, workspace, and session state."
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
  },
  help: {
    eyebrow: "Help",
    title: "Help and troubleshooting",
    summary: "Fix setup, Ollama, interface, tool, and local-state issues."
  }
};

const STORAGE_KEYS = {
  schema: "showcase.ui.schema.v1",
  sessions: "showcase.ui.sessions.v3",
  activeSession: "showcase.ui.activeSession.v3",
  memories: "showcase.ui.memories.v3",
  settings: "showcase.ui.settings.v3",
  systemPrompt: "showcase.ui.systemPrompt.v3",
  systemPrompts: "showcase.ui.systemPrompts.v1",
  activeSystemPrompt: "showcase.ui.activeSystemPrompt.v1",
  profile: "showcase.ui.profile.v1"
};

const LOCAL_STORAGE_SCHEMA_VERSION = 3;

const state = {
  sessions: [],
  activeSessionId: null,
  memories: [],
  models: [],
  benchmarkProfiles: [],
  benchmarks: { models: {}, profiles: {} },
  tools: [],
  toolCards: [],
  adapters: [],
  journal: [],
  journalStats: {},
  runtime: null,
  modelsOk: null,
  toolsError: "",
  settings: structuredClone(DEFAULT_SETTINGS),
  systemPrompts: [],
  activeSystemPromptId: null,
  profile: structuredClone(DEFAULT_PROFILE),
  busy: false,
  lastController: null,
  pendingConfirm: null,
  detailPayload: null,
  retryMessageId: null,
  editingMessageId: null,
  sessionSearchQuery: "",
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

function renderInlineMarkdown(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

function renderMarkdownBlocks(text) {
  const lines = String(text || "").split("\n");
  const html = [];
  let paragraph = [];
  let listType = null;
  let listItems = [];

  const flushParagraph = () => {
    if (!paragraph.length) return;
    html.push(`<p>${renderInlineMarkdown(paragraph.join(" "))}</p>`);
    paragraph = [];
  };
  const flushList = () => {
    if (!listType) return;
    html.push(`<${listType}>${listItems.map((item) => `<li>${renderInlineMarkdown(item)}</li>`).join("")}</${listType}>`);
    listType = null;
    listItems = [];
  };

  lines.forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushParagraph();
      flushList();
      return;
    }
    const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      flushList();
      const level = heading[1].length + 2;
      html.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
      return;
    }
    const unordered = trimmed.match(/^[-*]\s+(.+)$/);
    if (unordered) {
      flushParagraph();
      if (listType && listType !== "ul") flushList();
      listType = "ul";
      listItems.push(unordered[1]);
      return;
    }
    const ordered = trimmed.match(/^\d+\.\s+(.+)$/);
    if (ordered) {
      flushParagraph();
      if (listType && listType !== "ol") flushList();
      listType = "ol";
      listItems.push(ordered[1]);
      return;
    }
    flushList();
    paragraph.push(trimmed);
  });
  flushParagraph();
  flushList();
  return html.join("");
}

function renderSafeMarkdown(text) {
  const source = String(text || "");
  const parts = [];
  const fence = /```([\w.+-]*)\n?([\s\S]*?)```/g;
  let cursor = 0;
  let match;
  while ((match = fence.exec(source))) {
    if (match.index > cursor) parts.push(renderMarkdownBlocks(source.slice(cursor, match.index)));
    const language = match[1] ? ` data-language="${escapeHtml(match[1])}"` : "";
    parts.push(`<pre class="markdown-code"${language}><code>${escapeHtml(match[2].replace(/^\n|\n$/g, ""))}</code></pre>`);
    cursor = fence.lastIndex;
  }
  if (cursor < source.length) parts.push(renderMarkdownBlocks(source.slice(cursor)));
  return parts.join("") || "";
}

function renderMessageContent(root, message) {
  if (message.role === "assistant") {
    root.classList.add("rendered");
    root.innerHTML = renderSafeMarkdown(message.content || "");
    return;
  }
  root.classList.remove("rendered");
  root.textContent = message.content || "";
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

function hexToRgba(hex, alpha = 1) {
  const clean = String(hex || "").replace("#", "");
  if (!/^[0-9a-f]{6}$/i.test(clean)) return "rgba(19, 38, 30, 0.78)";
  const value = Number.parseInt(clean, 16);
  const r = (value >> 16) & 255;
  const g = (value >> 8) & 255;
  const b = value & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function fontStack(choice) {
  const stacks = {
    system: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    serif: 'Charter, "Iowan Old Style", Georgia, ui-serif, serif',
    mono: '"SFMono-Regular", "Cascadia Code", "Roboto Mono", Consolas, monospace',
    rounded: 'ui-rounded, "SF Pro Rounded", Nunito, Inter, ui-sans-serif, system-ui, sans-serif'
  };
  return stacks[choice] || stacks.system;
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
  const profiles = activeModelProfiles();
  for (const [category, pattern] of ROUTE_PATTERNS) {
    if (pattern.test(text)) return profiles.find((profile) => profile.category === category && profile.chat_capable);
  }
  return profiles.find((profile) => profile.category === "general");
}

function activeModelProfiles() {
  return Array.isArray(state.benchmarkProfiles) ? state.benchmarkProfiles : [];
}

function activeSession() {
  return state.sessions.find((session) => session.id === state.activeSessionId) ?? state.sessions[0];
}

function activeSystemPrompt() {
  return state.systemPrompts.find((prompt) => prompt.id === state.activeSystemPromptId) || null;
}

function profileHasContent(profile = state.profile) {
  return Object.values(profile || {}).some((value) => String(value || "").trim());
}

function makeMessageVariant(message, extra = {}) {
  return {
    id: extra.variantId || uid("variant"),
    content: extra.content ?? message.content ?? "",
    thinking: extra.thinking ?? message.thinking ?? "",
    toolCalls: extra.toolCalls ?? message.toolCalls ?? [],
    createdAt: extra.createdAt ?? message.createdAt ?? new Date().toISOString(),
    ok: extra.ok ?? message.ok ?? true,
    model: extra.model ?? message.model ?? null,
    options: extra.options ?? message.options ?? null,
    modelRoute: extra.modelRoute ?? message.modelRoute ?? null,
    latencyMs: extra.latencyMs ?? message.latencyMs ?? null,
    requestText: extra.requestText ?? message.requestText ?? null,
    editMeta: extra.editMeta ?? null,
    retryMeta: extra.retryMeta ?? null
  };
}

function syncMessageFromActiveVariant(message) {
  const variants = Array.isArray(message.variants) ? message.variants : [];
  if (!variants.length) return message;
  const index = Math.max(0, Math.min(Number(message.activeVariant) || 0, variants.length - 1));
  message.activeVariant = index;
  const variant = variants[index];
  ["content", "thinking", "toolCalls", "createdAt", "ok", "model", "options", "modelRoute", "latencyMs", "requestText", "editMeta", "retryMeta"].forEach((key) => {
    message[key] = variant[key];
  });
  return message;
}

function ensureMessageVariants(message) {
  if (!message) return null;
  if (!Array.isArray(message.variants) || !message.variants.length) {
    message.variants = [makeMessageVariant(message, { variantId: uid("variant") })];
    message.activeVariant = 0;
  }
  return syncMessageFromActiveVariant(message);
}

function activeMessageVariant(message) {
  ensureMessageVariants(message);
  return message.variants[message.activeVariant || 0];
}

function addMessageVariant(message, extra = {}) {
  ensureMessageVariants(message);
  const variant = makeMessageVariant(message, extra);
  message.variants.push(variant);
  message.activeVariant = message.variants.length - 1;
  syncMessageFromActiveVariant(message);
  return variant;
}

function patchActiveMessageVariant(message, patch) {
  const variant = activeMessageVariant(message);
  Object.assign(variant, patch);
  syncMessageFromActiveVariant(message);
  return variant;
}

function setMessageVariant(message, index) {
  ensureMessageVariants(message);
  message.activeVariant = Math.max(0, Math.min(index, message.variants.length - 1));
  syncMessageFromActiveVariant(message);
}

function normalizeSessionMessages(session) {
  (session?.messages || []).forEach((message) => ensureMessageVariants(message));
}

function messageIndex(messageId) {
  const session = activeSession();
  return session?.messages?.findIndex((message) => message.id === messageId) ?? -1;
}

function findPreviousUserMessage(messageId) {
  const session = activeSession();
  const index = messageIndex(messageId);
  if (!session || index < 0) return null;
  for (let i = index - 1; i >= 0; i -= 1) {
    if (session.messages[i].role === "user") return session.messages[i];
  }
  return null;
}

function findPairedAssistantMessage(userMessageId) {
  const session = activeSession();
  const index = messageIndex(userMessageId);
  if (!session || index < 0) return null;
  for (let i = index + 1; i < session.messages.length; i += 1) {
    const message = session.messages[i];
    if (message.role === "user") return null;
    if (message.role === "assistant") return message;
  }
  return null;
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
  state.sessions.forEach((session) => normalizeSessionMessages(session));
  localStorage.setItem(STORAGE_KEYS.schema, String(LOCAL_STORAGE_SCHEMA_VERSION));
  localStorage.setItem(STORAGE_KEYS.sessions, JSON.stringify(state.sessions));
  localStorage.setItem(STORAGE_KEYS.activeSession, state.activeSessionId ?? "");
  localStorage.setItem(STORAGE_KEYS.memories, JSON.stringify(state.memories));
  localStorage.setItem(STORAGE_KEYS.settings, JSON.stringify(state.settings));
  localStorage.setItem(STORAGE_KEYS.systemPrompt, $("systemPromptInput").value);
  localStorage.setItem(STORAGE_KEYS.systemPrompts, JSON.stringify(state.systemPrompts));
  localStorage.setItem(STORAGE_KEYS.activeSystemPrompt, state.activeSystemPromptId ?? "");
  localStorage.setItem(STORAGE_KEYS.profile, JSON.stringify(state.profile));
}

function loadLocalState() {
  const storedSchema = Number(localStorage.getItem(STORAGE_KEYS.schema) || 0);
  const oldSessions = localStorage.getItem("showcase.ui.sessions.v2");
  const oldActive = localStorage.getItem("showcase.ui.activeSession.v2");
  const oldMemories = localStorage.getItem("showcase.ui.memories.v2");
  const oldSettingsPrompt = localStorage.getItem("showcase.ui.systemPrompt.v2");
  try { state.sessions = JSON.parse(localStorage.getItem(STORAGE_KEYS.sessions) || oldSessions || "[]"); } catch { state.sessions = []; }
  try { state.memories = JSON.parse(localStorage.getItem(STORAGE_KEYS.memories) || oldMemories || "[]"); } catch { state.memories = []; }
  try { state.settings = deepMerge(DEFAULT_SETTINGS, JSON.parse(localStorage.getItem(STORAGE_KEYS.settings) || "{}")); } catch { state.settings = structuredClone(DEFAULT_SETTINGS); }
  try { state.systemPrompts = JSON.parse(localStorage.getItem(STORAGE_KEYS.systemPrompts) || "[]"); } catch { state.systemPrompts = []; }
  try { state.profile = deepMerge(DEFAULT_PROFILE, JSON.parse(localStorage.getItem(STORAGE_KEYS.profile) || "{}")); } catch { state.profile = structuredClone(DEFAULT_PROFILE); }
  state.activeSessionId = localStorage.getItem(STORAGE_KEYS.activeSession) || oldActive || null;
  const legacyPrompt = localStorage.getItem(STORAGE_KEYS.systemPrompt) || oldSettingsPrompt || "";
  state.activeSystemPromptId = localStorage.getItem(STORAGE_KEYS.activeSystemPrompt) || null;
  if (!state.systemPrompts.length && legacyPrompt.trim()) {
    const prompt = { id: uid("prompt"), title: "Imported prompt", shortMessage: "Legacy system prompt", context: "", fullPrompt: legacyPrompt.trim(), createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
    state.systemPrompts.push(prompt);
    state.activeSystemPromptId = prompt.id;
  }
  if (state.activeSystemPromptId && !state.systemPrompts.some((prompt) => prompt.id === state.activeSystemPromptId)) state.activeSystemPromptId = null;
  $("systemPromptInput").value = activeSystemPrompt()?.fullPrompt || legacyPrompt || "";
  state.sessions.forEach((session) => normalizeSessionMessages(session));
  if (storedSchema !== LOCAL_STORAGE_SCHEMA_VERSION) localStorage.setItem(STORAGE_KEYS.schema, String(LOCAL_STORAGE_SCHEMA_VERSION));
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
  const createdAt = new Date().toISOString();
  const message = {
    id: uid("msg"),
    role,
    content: content ?? "",
    thinking: extra.thinking ?? "",
    toolCalls: extra.toolCalls ?? [],
    createdAt,
    ok: extra.ok ?? true,
    model: extra.model ?? null,
    options: extra.options ?? null,
    modelRoute: extra.modelRoute ?? null,
    latencyMs: extra.latencyMs ?? null,
    requestText: extra.requestText ?? null,
    parentUserMessageId: extra.parentUserMessageId ?? null,
    activeVariant: 0,
    variants: []
  };
  message.variants = [makeMessageVariant(message, { createdAt })];
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
  renderRuntimeStatus();
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
  const session = activeSession();
  const messages = state.sessions.reduce((sum, item) => sum + (item.messages?.length || 0), 0);
  const toolCalls = state.sessions.reduce((sum, item) => sum + (item.messages || []).reduce((inner, msg) => inner + (msg.toolCalls || []).length, 0), 0);
  const overview = $("overviewGrid");
  if (overview) {
    overview.innerHTML = `
    <div class="overview-tile"><strong>${state.sessions.length}</strong><span>sessions</span></div>
    <div class="overview-tile"><strong>${state.tools.length || "-"}</strong><span>tools</span></div>
    <div class="overview-tile"><strong>${state.journal.length || "-"}</strong><span>events loaded</span></div>
    <div class="overview-tile"><strong>${state.memories.length}</strong><span>memories</span></div>
    <div class="overview-tile"><strong>${state.adapters.length || "-"}</strong><span>adapters</span></div>
    <div class="overview-tile"><strong>${toolCalls}</strong><span>tool calls</span></div>`;
  }
  const sessionInfo = $("sessionInfoGrid");
  if (sessionInfo) {
    const currentMessages = session?.messages?.length || 0;
    const updated = session?.messages?.at(-1)?.createdAt || session?.createdAt;
    sessionInfo.innerHTML = `
      <div class="overview-tile"><strong>${currentMessages}</strong><span>active messages</span></div>
      <div class="overview-tile"><strong>${messages}</strong><span>all messages</span></div>
      <div class="overview-tile"><strong>${session?.title ? escapeHtml(session.title).slice(0, 18) : "New"}</strong><span>active session</span></div>
      <div class="overview-tile"><strong>${updated ? new Date(updated).toLocaleDateString() : "-"}</strong><span>last update</span></div>`;
  }
  renderRecentSessions();
}

function plannerSafeToolCount() {
  return state.tools.map((tool) => toolId(tool)).filter((id) => PLANNER_SAFE_TOOLS.has(id)).length;
}

function runtimeReadiness() {
  const selectedModel = $("modelSelect")?.value || "auto route";
  const toolTotal = state.tools.length || state.runtime?.tools?.length || 0;
  const adapterTotal = state.adapters.length || state.runtime?.adapters?.length || 0;
  const journalKnown = Boolean(state.journalStats.path || state.runtime?.journal?.path || state.journal.length);
  return [
    { label: "Ollama", value: state.modelsOk === null ? "checking" : state.modelsOk ? "online" : "offline", status: state.modelsOk ? "ok" : state.modelsOk === false ? "bad" : "muted", detail: state.modelsOk ? `${state.models.length} local models` : "start Ollama or check endpoint" },
    { label: "Model", value: selectedModel, status: selectedModel === "auto route" ? "muted" : "ok", detail: selectedModel === "auto route" ? "server routing enabled" : "manual override" },
    { label: "Tools", value: `${plannerSafeToolCount()}/${toolTotal || "-"}`, status: toolTotal ? "ok" : "bad", detail: "planner-safe / runtime" },
    { label: "Workspace", value: adapterTotal ? `${adapterTotal} adapters` : "workspace", status: adapterTotal ? "ok" : "warn", detail: adapterTotal ? "adapter inventory ready" : "no adapters loaded yet" },
    { label: "Journal", value: journalKnown ? "active" : "empty", status: "muted", detail: state.journal.length ? `${state.journal.length} events loaded` : "events appear after requests" }
  ];
}

function renderRuntimeStatus() {
  const root = $("runtimeStatusStrip");
  if (!root) return;
  root.innerHTML = runtimeReadiness().map((item) => `
    <div class="runtime-tile ${item.status}">
      <span>${escapeHtml(item.label)}</span>
      <strong>${escapeHtml(item.value)}</strong>
      <small>${escapeHtml(item.detail)}</small>
    </div>`).join("");
}

async function loadRuntime() {
  try {
    const res = await fetch("/api/runtime");
    state.runtime = await res.json();
  } catch (error) {
    state.runtime = { ok: false, error: error.message };
  } finally {
    renderRuntimeStatus();
  }
}

function renderSessions() {
  const root = $("sessionList");
  root.innerHTML = "";
  const query = state.sessionSearchQuery.trim().toLowerCase();
  const sessions = query
    ? state.sessions.filter((session) => JSON.stringify(session).toLowerCase().includes(query))
    : state.sessions;
  if (!sessions.length) {
    root.innerHTML = `<div class="session-item diagnostic-card"><strong>No matching chats</strong><span>Search did not match local session titles or messages.</span></div>`;
    renderRecentSessions();
    return;
  }
  sessions.forEach((session) => {
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
  renderRecentSessions();
}

function renderRecentSessions() {
  const root = $("recentSessionsPullout");
  const sidebarRoot = $("sidebarSessionHistory");
  const recent = [...state.sessions]
    .sort((a, b) => new Date(b.messages?.at(-1)?.createdAt || b.createdAt) - new Date(a.messages?.at(-1)?.createdAt || a.createdAt))
    .slice(0, 6);
  renderSidebarSessionHistory(sidebarRoot, recent);
  if (!root) return;
  if (!recent.length) {
    root.innerHTML = `<div class="recent-empty">No chats yet.</div>`;
    return;
  }
  root.innerHTML = `<div class="recent-pullout-title">Session history</div>` + recent.map((session) => recentSessionButtonHtml(session)).join("");
  wireSessionHistoryButtons(root);
}

function renderSidebarSessionHistory(root, recent) {
  if (!root) return;
  const visible = recent.slice(0, 4);
  if (!visible.length) {
    root.innerHTML = `<div class="recent-empty">No chats yet.</div>`;
    return;
  }
  root.innerHTML = visible.map((session) => recentSessionButtonHtml(session)).join("");
  wireSessionHistoryButtons(root);
}

function recentSessionButtonHtml(session) {
  const lastMessage = [...(session.messages || [])].reverse().find((message) => String(message.content || "").trim());
  const snippet = String(lastMessage?.content || "New conversation").replace(/\s+/g, " ").trim().slice(0, 72);
  const updated = session.messages?.at(-1)?.createdAt || session.createdAt;
  return `
    <button class="recent-session-button ${session.id === state.activeSessionId ? "active" : ""}" data-session-id="${escapeHtml(session.id)}">
      <strong>${escapeHtml(session.title || "New session")}</strong>
      <span>${escapeHtml(snippet || `${session.messages?.length || 0} messages`)}</span>
      <small>${session.messages?.length || 0} messages · ${new Date(updated).toLocaleDateString()}</small>
    </button>`;
}

function wireSessionHistoryButtons(root) {
  root.querySelectorAll("[data-session-id]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      state.activeSessionId = button.dataset.sessionId;
      const pullout = $("recentSessionsPullout");
      if (pullout) pullout.hidden = true;
      persist();
      renderAll();
      setActivePage("chat");
    });
  });
}

function toggleRecentSessionsPullout() {
  const root = $("recentSessionsPullout");
  if (!root) return;
  renderRecentSessions();
  root.hidden = !root.hidden;
}

function searchSessions() {
  const value = prompt("Search chats:", state.sessionSearchQuery || "");
  if (value === null) return;
  state.sessionSearchQuery = value.trim();
  setActivePage("sessions");
  renderSessions();
}

function toggleSidebarCollapsed() {
  state.settings.sidebarCollapsed = !state.settings.sidebarCollapsed;
  applySettingsVisuals();
  persist();
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
  normalizeSessionMessages(session);
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
  ensureMessageVariants(message);
  const node = template.content.firstElementChild.cloneNode(true);
  node.classList.add(message.role);
  node.classList.toggle("failed", message.ok === false);
  node.dataset.messageId = message.id;
  applyMessageAvatar(node, message.role);
  node.querySelector(".message-role").textContent = message.role === "user" ? "You" : message.role === "tool" ? "Tool" : "Assistant";
  node.querySelector(".message-time").textContent = new Date(message.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const contentRoot = node.querySelector(".message-content");
  if (state.editingMessageId === message.id && message.role === "user") {
    contentRoot.classList.remove("rendered");
    renderInlineEditor(contentRoot, message);
  } else {
    renderMessageContent(contentRoot, message);
  }
  renderActivityBox(node, message);
  renderMessageActions(node, message);
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
    if (event.target.closest("button, details, summary, pre, textarea, input, select, .message-actions, .inline-edit-box")) return;
    openMessageDetail(message);
  });
  chatLog.appendChild(node);
  return node;
}

function applyMessageAvatar(node, role) {
  const avatar = node.querySelector(".avatar");
  const image = role === "user" ? state.profile.userAvatar : role === "assistant" ? state.profile.assistantAvatar : "";
  if (!avatar || !image) return;
  avatar.style.backgroundImage = `url(${image})`;
  avatar.style.backgroundSize = "cover";
  avatar.style.backgroundPosition = "center";
}

function renderInlineEditor(root, message) {
  root.innerHTML = `
    <div class="inline-edit-box">
      <textarea class="code-input inline-edit-input" rows="5">${escapeHtml(message.content || "")}</textarea>
      <div class="inline-edit-actions">
        <button class="ghost-button" data-edit-action="cancel">Cancel</button>
        <button class="primary-button" data-edit-action="save">Save edit and rerun</button>
      </div>
    </div>`;
  const textarea = root.querySelector("textarea");
  textarea.focus();
  textarea.setSelectionRange(textarea.value.length, textarea.value.length);
  root.querySelector('[data-edit-action="cancel"]').addEventListener("click", (event) => {
    event.stopPropagation();
    state.editingMessageId = null;
    renderChat();
  });
  root.querySelector('[data-edit-action="save"]').addEventListener("click", (event) => {
    event.stopPropagation();
    finishUserMessageEdit(message.id, textarea.value);
  });
}

function renderMessageActions(node, message) {
  const root = node.querySelector(".message-actions");
  const sources = collectSources(message);
  const variantCount = message.variants?.length || 1;
  const canVariant = variantCount > 1;
  const parts = [];
  if (canVariant) {
    parts.push(`
      <div class="variant-switcher" title="Message variants">
        <button class="ghost-button" data-message-action="variant-prev">&lt;</button>
        <span>${(message.activeVariant || 0) + 1} of ${variantCount}</span>
        <button class="ghost-button" data-message-action="variant-next">&gt;</button>
      </div>`);
  }
  if (message.role === "user") parts.push('<button class="ghost-button" data-message-action="edit">Edit</button>');
  if (message.role === "assistant") {
    parts.push('<button class="ghost-button" data-message-action="retry">Retry</button>');
    if (message.ok === false) parts.push('<button class="ghost-button" data-message-action="edit-prev">Edit prompt</button>');
  }
  if (sources.length) parts.push(`<button class="ghost-button" data-message-action="sources">Sources (${sources.length})</button>`);
  if (message.ok === false) parts.push('<button class="danger-button" data-message-action="debug">Debug</button>');
  root.innerHTML = parts.join("");
  root.hidden = !parts.length;
  root.querySelectorAll("button").forEach((button) => button.addEventListener("click", (event) => {
    event.stopPropagation();
    handleMessageAction(message, button.dataset.messageAction);
  }));
}

function handleMessageAction(message, action) {
  if (!action) return;
  if (action === "edit") return startUserMessageEdit(message.id);
  if (action === "edit-prev") {
    const user = findPreviousUserMessage(message.id);
    if (user) startUserMessageEdit(user.id);
    return;
  }
  if (action === "retry") return openRetryDialog(message);
  if (action === "debug") return openMessageDetail(message);
  if (action === "sources") return openSourcesDetail(message);
  if (action === "variant-prev" || action === "variant-next") {
    const count = message.variants?.length || 1;
    const delta = action === "variant-prev" ? -1 : 1;
    const next = ((message.activeVariant || 0) + delta + count) % count;
    setMessageVariant(message, next);
    if (message.role === "user") {
      const paired = findPairedAssistantMessage(message.id);
      if (paired && (paired.variants?.length || 0) > next) setMessageVariant(paired, next);
    }
    persist();
    renderChat();
  }
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
  box.open = Boolean(state.settings.openThinking);
  title.textContent = hasThinking ? (hasTools ? "Thinking + tool use" : "Thinking") : "Tool use";
  meta.textContent = hasTools ? `${calls.length} tool${calls.length === 1 ? "" : "s"}` : "";
  thinkingContent.hidden = !hasThinking;
  thinkingContent.textContent = hasThinking ? formatActivityThinking(message.thinking, calls) : "";
  renderToolPipeline(node, calls);
  renderToolCalls(toolsRoot, calls, { nested: true });
}

function renderToolPipeline(node, calls) {
  const toolsRoot = node.querySelector(".activity-tool-stack");
  let root = node.querySelector(".tool-pipeline-summary");
  if (!root) {
    root = document.createElement("div");
    root.className = "tool-pipeline-summary";
    toolsRoot.before(root);
  }
  root.hidden = !calls.length;
  root.innerHTML = calls.map((call, index) => `
    <div class="tool-pipeline-step ${call.ok === null ? "" : (call.ok ? "ok" : "bad")}">
      <span>${index + 1}</span>
      <strong>${escapeHtml(call.tool_name || call.name || "tool")}</strong>
      <small>${call.ok === null ? "running" : (call.ok ? "ok" : "failed")}</small>
    </div>`).join("");
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
    const pending = call.ok === null || call.data?.status === "running";
    const rawSummary = call.summary || JSON.stringify(call.data ?? call, null, 2);
    const summary = escapeHtml(String(rawSummary).length > 900 ? `${String(rawSummary).slice(0, 900)}\n... [open details for full output]` : rawSummary);
    const payload = escapeHtml(JSON.stringify(call, null, 2));
    card.innerHTML = `
      ${nested
        ? `<summary><strong>${escapeHtml(call.tool_name || call.name || "tool")}</strong><span class="${pending ? "" : (call.ok ? "ok-text" : "bad-text")}">${pending ? "running" : (call.ok ? "ok" : "failed")}</span></summary>`
        : `<header><strong>${escapeHtml(call.tool_name || call.name || "tool")}</strong><span class="${pending ? "" : (call.ok ? "ok-text" : "bad-text")}">${pending ? "running" : (call.ok ? "ok" : "failed")}</span></header>`}
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

function collectSources(message) {
  const sources = [];
  (message.toolCalls || []).forEach((call, callIndex) => {
    const tool = call.tool_name || call.name || "tool";
    const data = call.data || {};
    const base = { tool, callIndex: callIndex + 1, ok: call.ok !== false };
    if (tool === "web_search") {
      (data.results || []).slice(0, 12).forEach((item, index) => {
        const title = item.title || item.Text || item.Heading || `Web result ${index + 1}`;
        const url = item.url || item.FirstURL || item.Result || "";
        sources.push({ ...base, type: "web", title, url, snippet: item.snippet || item.Text || "" });
      });
      if (!sources.some((source) => source.callIndex === callIndex + 1) && data.query) {
        sources.push({ ...base, type: "web", title: `Web search: ${data.query}`, url: "", snippet: call.summary || "" });
      }
    } else if (["fetch_url", "extract_webpage_content", "expand_search_result", "parse_json_api", "download_file"].includes(tool)) {
      const url = data.url || data.source_url || "";
      if (url) sources.push({ ...base, type: "web", title: url, url, snippet: call.summary || "" });
    } else if (["weather_lookup", "latest_linux_kernel"].includes(tool)) {
      sources.push({ ...base, type: "web", title: tool === "weather_lookup" ? "Weather API" : "kernel.org releases", url: tool === "weather_lookup" ? "https://open-meteo.com/" : "https://www.kernel.org/releases.json", snippet: call.summary || "" });
    } else if (tool === "library_search") {
      (data.results || []).forEach((item) => {
        sources.push({ ...base, type: item.type === "zim" ? "kiwix" : "library", title: item.title || item.id || "Library item", url: item.path || "", snippet: item.snippet || "", raw: item });
      });
    } else if (tool === "library_read_epub" || tool === "library_read_zim") {
      sources.push({ ...base, type: tool === "library_read_zim" ? "kiwix" : "library", title: data.title || data.id || tool, url: data.path || data.source || "", snippet: call.summary || "", raw: data });
    } else if (["read_file", "file_search", "content_search", "grep_search", "tree_view", "list_directory", "get_file_info"].includes(tool)) {
      const matches = Array.isArray(data.matches) ? data.matches : [];
      if (matches.length) {
        matches.slice(0, 25).forEach((item) => {
          if (typeof item === "string") sources.push({ ...base, type: "file", title: item, url: item, snippet: "" });
          else sources.push({ ...base, type: "file", title: item.path || "Workspace file", url: item.path || "", snippet: item.line ? `Line ${item.line}: ${item.text || ""}` : item.text || "", raw: item });
        });
      } else if (data.path) {
        sources.push({ ...base, type: "file", title: data.path, url: data.path, snippet: call.summary || "" });
      }
    } else if (tool === "query_index" || tool === "list_indexed_sources") {
      const labels = [...String(call.summary || "").matchAll(/^Source:\s*(.+)$/gm)].map((match) => match[1]);
      if (labels.length) labels.forEach((label) => sources.push({ ...base, type: "index", title: label, url: label, snippet: "" }));
      else sources.push({ ...base, type: "index", title: "Local index", url: data.path || "", snippet: call.summary || "" });
    }
  });
  return sources;
}

function openSourcesDetail(message) {
  const sources = collectSources(message);
  const groups = ["web", "library", "kiwix", "file", "index"]
    .map((type) => ({ type, items: sources.filter((source) => source.type === type) }))
    .filter((group) => group.items.length);
  if (!groups.length) return openMessageDetail(message);
  const first = groups[0].type;
  const tabs = groups.map((group) => `<button class="source-tab ${group.type === first ? "active" : ""}" data-source-tab="${group.type}">${escapeHtml(group.type)} (${group.items.length})</button>`).join("");
  const panels = groups.map((group) => `
    <div class="source-panel ${group.type === first ? "active" : ""}" data-source-panel="${group.type}">
      ${group.items.map((source, index) => renderSourceCard(source, group.type, index)).join("")}
    </div>`).join("");
  openDetailModal({
    eyebrow: "Sources",
    title: `${sources.length} source${sources.length === 1 ? "" : "s"}`,
    html: `<div class="source-tabs">${tabs}</div>${panels}<h3>Raw sources</h3>${jsonBlock(sources)}`,
    payload: sources
  });
  bindSourceTabs();
}

function renderSourceCard(source, groupType, index) {
  const title = source.title || `${groupType} source ${index + 1}`;
  const link = source.type === "web" ? safeHttpUrl(source.url) : "";
  const titleHtml = link
    ? `<a class="source-title-link" href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer"><strong>${escapeHtml(title)}</strong></a>`
    : `<strong>${escapeHtml(title)}</strong>`;
  const urlHtml = source.url
    ? link
      ? `<a class="source-url-link" href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer"><code>${escapeHtml(source.url)}</code></a>`
      : `<code>${escapeHtml(source.url)}</code>`
    : "";
  return `
    <section class="source-card ${link ? "hotlink-source" : ""}">
      <div>${titleHtml}<span>${escapeHtml(source.tool)} call ${source.callIndex}</span></div>
      ${urlHtml}
      ${source.snippet ? `<pre>${escapeHtml(String(source.snippet).slice(0, 1800))}</pre>` : ""}
    </section>`;
}

function safeHttpUrl(value) {
  const url = String(value || "").trim();
  if (!url) return "";
  try {
    const parsed = new URL(url);
    return ["http:", "https:"].includes(parsed.protocol) ? parsed.href : "";
  } catch {
    return "";
  }
}

function bindSourceTabs() {
  document.querySelectorAll(".source-tab").forEach((button) => {
    button.addEventListener("click", () => {
      const type = button.dataset.sourceTab;
      document.querySelectorAll(".source-tab").forEach((candidate) => candidate.classList.toggle("active", candidate === button));
      document.querySelectorAll(".source-panel").forEach((panel) => panel.classList.toggle("active", panel.dataset.sourcePanel === type));
    });
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
    state.benchmarks = data.benchmarks && typeof data.benchmarks === "object" ? data.benchmarks : { models: {}, profiles: {} };
    state.benchmarkProfiles = Array.isArray(data.profiles) ? data.profiles : [];
    state.modelsOk = Boolean(data.ok);
    $("modelStatus").textContent = data.ok ? `${liveModels.length} local` : "offline";
    $("modelStatus").className = `status-pill ${data.ok ? "ok" : "bad"}`;
    if (!data.ok && data.error) renderModelMeta(`Ollama models could not be loaded: ${data.error}`);
  } catch (error) {
    state.modelsOk = false;
    state.models = [];
    state.benchmarks = { models: {}, profiles: {} };
    state.benchmarkProfiles = [];
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

  appendBenchmarkProfileOptions(select, seen, { includeDisabled: true });
  updateModelMeta();
  renderRuntimeStatus();
}

function appendBenchmarkProfileOptions(select, seen, { includeDisabled = false } = {}) {
  const profiles = activeModelProfiles().filter((profile) => profile?.model && !seen.has(profile.model));
  if (!profiles.length) return;
  const group = document.createElement("optgroup");
  group.label = "Benchmarked profiles";
  profiles.forEach((profile) => {
    const option = document.createElement("option");
    option.value = profile.model;
    option.disabled = includeDisabled ? !profile.chat_capable : false;
    option.textContent = `${profile.model} · ${profile.category}${profile.benchmark_score ? ` · ${profile.benchmark_score}` : ""}`;
    group.appendChild(option);
    seen.add(profile.model);
  });
  select.appendChild(group);
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
  const profile = activeModelProfiles().find((item) => item.model === value) || null;
  const live = state.models.find((item) => item.name === value || item.model === value) || null;
  const root = $("modelMeta");
  if (!value) {
    root.innerHTML = `<div class="model-card clickable-card"><strong>Auto route</strong><span>Server picks per request.</span></div>`;
  } else {
    root.innerHTML = `
      <div class="model-card clickable-card">
        <strong>${escapeHtml(value)}</strong>
        <span>${escapeHtml(profile?.category || live?.details?.family || "local model")}${live?.size ? ` · ${escapeHtml(prettyBytes(live.size))}` : ""}</span>
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
  appendBenchmarkProfileOptions(select, seen);
  select.value = current;
}

async function loadTools() {
  try {
    const res = await fetch("/api/tools");
    const data = await res.json();
    state.tools = Array.isArray(data.tools) ? data.tools : [];
    state.toolCards = Array.isArray(data.tool_cards) ? data.tool_cards : state.tools.map((tool) => ({ id: tool }));
    state.toolsError = "";
  } catch (error) {
    state.toolsError = error.message;
    state.tools = Object.keys(TOOL_EXAMPLES);
    state.toolCards = state.tools.map((tool) => ({ id: tool }));
  }
  if (!state.tools.length) state.tools = Object.keys(TOOL_EXAMPLES);
  if (!state.toolCards.length) state.toolCards = state.tools.map((tool) => ({ id: tool }));
  renderTools();
  renderToolPresets();
  renderRuntimeStatus();
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
  if (state.toolsError) {
    list.innerHTML = `<div class="tool-item diagnostic-card"><strong>Using fallback tool docs</strong><span>/api/tools failed: ${escapeHtml(state.toolsError)}</span></div>`;
  }
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

function renderToolPresets() {
  const root = $("toolPresetGrid");
  if (!root) return;
  root.innerHTML = TOOL_PRESETS.map((preset) => `<button class="chip-button" data-tool-preset="${escapeHtml(preset.id)}">${escapeHtml(preset.label)}</button>`).join("");
  root.querySelectorAll("[data-tool-preset]").forEach((button) => {
    button.addEventListener("click", () => applyToolPreset(button.dataset.toolPreset));
  });
}

function applyToolPreset(presetId) {
  const preset = TOOL_PRESETS.find((candidate) => candidate.id === presetId);
  if (!preset) return;
  const select = $("toolSelect");
  if ([...select.options].some((option) => option.value === preset.tool)) {
    select.value = preset.tool;
  }
  $("toolArgs").value = JSON.stringify(preset.args, null, 2);
  $("toolResult").innerHTML = `<span>Preset loaded: ${escapeHtml(preset.label)}. Review arguments, then run.</span>`;
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
    renderRuntimeStatus();
  } catch (error) {
    root.innerHTML = `<div class="adapter-item clickable-card diagnostic-card"><strong>No adapters loaded</strong><span>${escapeHtml(error.message)}. Check TOOLING_SHOWCASE_PORTFOLIO or expected sibling project paths.</span></div>`;
    renderRuntimeStatus();
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
      renderRuntimeStatus();
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
    renderRuntimeStatus();
  } catch (error) {
    root.innerHTML = `<div class="journal-item diagnostic-card"><strong>Journal unavailable</strong><span>${escapeHtml(error.message)}. Send a message or check the backend journal path.</span></div>`;
    renderRuntimeStatus();
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
  const prompt = activeSystemPrompt();
  const parts = [];
  if (prompt?.fullPrompt?.trim()) parts.push(prompt.fullPrompt.trim());
  if (prompt?.context?.trim()) parts.push(`Prompt context:\n${prompt.context.trim()}`);
  const legacy = $("systemPromptInput").value.trim();
  if (!prompt && legacy) parts.push(legacy);

  if ($("memoryToggle").checked && profileHasContent()) {
    const profileLines = [
      state.profile.name ? `Name: ${state.profile.name}` : "",
      state.profile.nickname ? `Nickname: ${state.profile.nickname}` : "",
      state.profile.about ? `About: ${state.profile.about}` : "",
      state.profile.preferences ? `User preferences: ${state.profile.preferences}` : "",
      state.profile.other ? `Other information: ${state.profile.other}` : ""
    ].filter(Boolean).join("\n");
    if (profileLines) parts.push(`${state.settings.profilePrefix || DEFAULT_SETTINGS.profilePrefix}:\n${profileLines}`);
  }

  if ($("memoryToggle").checked && state.memories.length) {
    const memories = state.memories.map((memory, index) => `${index + 1}. ${memory.title ? `${memory.title}: ` : ""}${memory.text}`).join("\n");
    const heading = state.settings.memoryPrefix || DEFAULT_SETTINGS.memoryPrefix;
    parts.push(`${heading}:\n${memories}`);
  }

  return parts.filter(Boolean).join("\n\n") || null;
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

function buildRuntimeTimeouts() {
  const timeouts = state.settings.runtimeTimeouts || DEFAULT_SETTINGS.runtimeTimeouts;
  return {
    ollama_timeout_seconds: Math.max(1, Math.min(3600, Number(timeouts.ollama) || DEFAULT_SETTINGS.runtimeTimeouts.ollama)),
    tool_timeout_seconds: Math.max(1, Math.min(3600, Number(timeouts.tools) || DEFAULT_SETTINGS.runtimeTimeouts.tools))
  };
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
  input.value = "";
  const modelOptions = buildModelOptions();
  const userMessage = addSessionMessage("user", text, { model: $("modelSelect").value || "auto" });
  chatLog.querySelector(".empty-state")?.remove();
  renderMessage(userMessage);
  const assistantMessage = addSessionMessage("assistant", "", { thinking: "", toolCalls: [], model: $("modelSelect").value || "auto", options: modelOptions, requestText: text, parentUserMessageId: userMessage.id });
  const assistantNode = renderMessage(assistantMessage);
  scrollChat();
  await requestAssistantResponse({ userText: text, requestText: text, assistantMessage, assistantNode });
}

async function requestAssistantResponse({ userText, requestText, assistantMessage, assistantNode = null, modelOverride = null, retryMeta = null }) {
  if (state.busy) return;
  state.busy = true;
  const started = performance.now();
  const modelOptions = buildModelOptions();
  const selectedModel = modelOverride !== null ? modelOverride : ($("modelSelect").value || null);
  patchActiveMessageVariant(assistantMessage, {
    content: "",
    thinking: "",
    toolCalls: [],
    ok: true,
    model: selectedModel || "auto",
    options: modelOptions,
    modelRoute: null,
    latencyMs: null,
    requestText: requestText || userText,
    retryMeta
  });
  if (!assistantNode || !assistantNode.isConnected) {
    renderChat();
    assistantNode = chatLog.querySelector(`[data-message-id="${assistantMessage.id}"]`);
  }
  if (!assistantNode) {
    state.busy = false;
    return;
  }
  const contentNode = assistantNode.querySelector(".message-content");
  const payload = {
    text: requestText || userText,
    confirm: $("confirmToggle").checked,
    stream: $("streamToggle").checked,
    model: selectedModel || null,
    system_prompt: buildSystemPrompt(),
    options: modelOptions,
    response_format: buildResponseFormat(),
    ...buildRuntimeTimeouts()
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
          patchActiveMessageVariant(assistantMessage, { content: `${assistantMessage.content || ""}${chunk.delta || ""}` });
          renderMessageContent(contentNode, assistantMessage);
        } else if (chunk.type === "thinking_delta") {
          patchActiveMessageVariant(assistantMessage, { thinking: `${assistantMessage.thinking || ""}${chunk.delta || ""}` });
          renderActivityBox(assistantNode, assistantMessage);
        } else if (chunk.type === "tool_calls") {
          patchActiveMessageVariant(assistantMessage, { toolCalls: chunk.tool_calls || [] });
          renderActivityBox(assistantNode, assistantMessage);
          renderMessageActions(assistantNode, assistantMessage);
        } else if (chunk.type === "tool_start") {
          patchActiveMessageVariant(assistantMessage, { toolCalls: upsertStreamingToolCall(assistantMessage.toolCalls || [], {
            tool_name: chunk.tool_name || "tool",
            ok: null,
            summary: "Running...",
            data: { arguments: chunk.arguments || {}, status: "running" }
          }) });
          renderActivityBox(assistantNode, assistantMessage);
          renderMessageActions(assistantNode, assistantMessage);
        } else if (chunk.type === "tool_result") {
          const nextCalls = chunk.tool_calls || upsertStreamingToolCall(assistantMessage.toolCalls || [], chunk.tool_call || {});
          patchActiveMessageVariant(assistantMessage, { toolCalls: nextCalls });
          renderActivityBox(assistantNode, assistantMessage);
          renderMessageActions(assistantNode, assistantMessage);
        } else if (chunk.type === "final") {
          const content = stripThinkTags(chunk.message || assistantMessage.content || "");
          const thinking = chunk.thinking || extractThinkText(chunk.message || "") || assistantMessage.thinking || "";
          patchActiveMessageVariant(assistantMessage, {
            ok: Boolean(chunk.ok),
            content,
            thinking,
            toolCalls: chunk.tool_calls || [],
            model: chunk.data?.model || assistantMessage.model,
            modelRoute: chunk.data?.model_route || null
          });
          assistantNode.classList.toggle("failed", assistantMessage.ok === false);
          renderMessageContent(contentNode, assistantMessage);
          renderActivityBox(assistantNode, assistantMessage);
          renderMessageActions(assistantNode, assistantMessage);
        }
        scrollChat();
      });
    } else {
      const data = await res.json();
      patchActiveMessageVariant(assistantMessage, {
        ok: Boolean(data.ok),
        content: stripThinkTags(data.message || ""),
        thinking: data.thinking || extractThinkText(data.message || ""),
        toolCalls: data.tool_calls || [],
        model: data.data?.model || assistantMessage.model,
        modelRoute: data.data?.model_route || null
      });
      assistantNode.classList.toggle("failed", assistantMessage.ok === false);
      renderMessageContent(contentNode, assistantMessage);
      renderActivityBox(assistantNode, assistantMessage);
      renderMessageActions(assistantNode, assistantMessage);
    }
  } catch (error) {
    patchActiveMessageVariant(assistantMessage, {
      ok: false,
      content: error.name === "AbortError" ? "Request stopped." : `Request failed: ${error.message}`
    });
    assistantNode.classList.toggle("failed", true);
    renderMessageContent(contentNode, assistantMessage);
    renderMessageActions(assistantNode, assistantMessage);
  } finally {
    patchActiveMessageVariant(assistantMessage, { latencyMs: Math.round(performance.now() - started) });
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

function upsertStreamingToolCall(calls, nextCall) {
  const next = { ...(nextCall || {}) };
  const name = next.tool_name || next.name || "tool";
  const args = JSON.stringify(next.data?.arguments || next.arguments || {});
  const index = calls.findIndex((call) => {
    const callName = call.tool_name || call.name || "tool";
    const callArgs = JSON.stringify(call.data?.arguments || call.arguments || {});
    return callName === name && (call.ok === null || call.data?.status === "running") && callArgs === args;
  });
  if (index === -1) return [...calls, next];
  return calls.map((call, callIndex) => callIndex === index ? { ...call, ...next } : call);
}

function startUserMessageEdit(messageId) {
  if (state.busy) return;
  state.editingMessageId = messageId;
  renderChat();
}

async function finishUserMessageEdit(messageId, nextText) {
  if (state.busy) return;
  const session = activeSession();
  const message = session?.messages?.find((candidate) => candidate.id === messageId);
  const text = String(nextText || "").trim();
  if (!message || !text) return;
  state.editingMessageId = null;
  addMessageVariant(message, {
    content: text,
    thinking: "",
    toolCalls: [],
    ok: true,
    model: $("modelSelect").value || "auto",
    requestText: text,
    editMeta: { editedAt: new Date().toISOString(), sourceVariant: message.variants.length }
  });
  let assistantMessage = findPairedAssistantMessage(message.id);
  if (!assistantMessage) {
    const userIndex = messageIndex(message.id);
    assistantMessage = {
      id: uid("msg"),
      role: "assistant",
      parentUserMessageId: message.id,
      activeVariant: 0,
      variants: [],
      content: "",
      thinking: "",
      toolCalls: [],
      createdAt: new Date().toISOString(),
      ok: true,
      model: $("modelSelect").value || "auto",
      options: buildModelOptions(),
      modelRoute: null,
      latencyMs: null,
      requestText: text
    };
    assistantMessage.variants = [makeMessageVariant(assistantMessage, { requestText: text })];
    session.messages.splice(Math.max(0, userIndex + 1), 0, assistantMessage);
  } else {
    addMessageVariant(assistantMessage, {
      content: "",
      thinking: "",
      toolCalls: [],
      ok: true,
      model: $("modelSelect").value || "auto",
      options: buildModelOptions(),
      requestText: text,
      editMeta: { userMessageId: message.id, editedAt: new Date().toISOString() }
    });
  }
  persist();
  renderChat();
  const assistantNode = chatLog.querySelector(`[data-message-id="${assistantMessage.id}"]`);
  await requestAssistantResponse({ userText: text, requestText: text, assistantMessage, assistantNode });
}

function openRetryDialog(message) {
  if (state.busy) return;
  state.retryMessageId = message.id;
  populateRetryModelSelect(message.model || $("modelSelect").value || "");
  $("retryStyleSelect").value = message.ok === false ? "debug" : "same";
  $("retryExtraInput").value = "";
  const user = findPreviousUserMessage(message.id);
  $("retryContextPreview").textContent = [
    `Previous user message:\n${user?.content || "(not found)"}`,
    `Previous assistant message:\n${message.content || "(empty)"}`
  ].join("\n\n");
  $("retryDialog").hidden = false;
  $("retryExtraInput").focus();
}

function closeRetryDialog() {
  state.retryMessageId = null;
  $("retryDialog").hidden = true;
}

function populateRetryModelSelect(currentModel) {
  const select = $("retryModelSelect");
  select.innerHTML = '<option value="">Auto route / current default</option>';
  const seen = new Set();
  state.models.forEach((model) => {
    const name = model.name || model.model;
    if (!name || seen.has(name)) return;
    seen.add(name);
    const option = document.createElement("option");
    option.value = name;
    option.textContent = `${name}${model.size ? ` - ${prettyBytes(model.size)}` : ""}`;
    select.appendChild(option);
  });
  appendBenchmarkProfileOptions(select, seen);
  select.value = currentModel && currentModel !== "auto" ? currentModel : "";
}

function buildRetryPrompt(userText, previousAssistantText, style, extraInput) {
  const styleMap = {
    same: "Regenerate the answer with the same intent, correcting any issues.",
    more_detail: "Regenerate with more detail, clearer reasoning, and fuller coverage.",
    concise: "Regenerate more concisely while preserving the important answer.",
    debug: "Debug the failed response, explain what went wrong if relevant, and provide a corrected answer.",
    creative: "Regenerate using a meaningfully different approach or framing."
  };
  return [
    userText,
    "",
    "Retry instructions:",
    styleMap[style] || styleMap.same,
    extraInput ? `Additional user input: ${extraInput}` : "",
    "",
    "Previous assistant response for context:",
    previousAssistantText || "(empty previous response)"
  ].filter((part) => part !== "").join("\n");
}

async function runRetryFromDialog() {
  const session = activeSession();
  const message = session?.messages?.find((candidate) => candidate.id === state.retryMessageId);
  if (!message || state.busy) return;
  const user = findPreviousUserMessage(message.id);
  if (!user) return;
  const previousAssistant = message.content || "";
  const style = $("retryStyleSelect").value;
  const extra = $("retryExtraInput").value.trim();
  const modelOverride = $("retryModelSelect").value || null;
  const requestText = buildRetryPrompt(user.content || "", previousAssistant, style, extra);
  addMessageVariant(message, {
    content: "",
    thinking: "",
    toolCalls: [],
    ok: true,
    model: modelOverride || message.model || "auto",
    options: buildModelOptions(),
    requestText,
    retryMeta: { retriedAt: new Date().toISOString(), style, extra, previousAssistant }
  });
  closeRetryDialog();
  persist();
  renderChat();
  const assistantNode = chatLog.querySelector(`[data-message-id="${message.id}"]`);
  await requestAssistantResponse({ userText: user.content || "", requestText, assistantMessage: message, assistantNode, modelOverride, retryMeta: { style, extra } });
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
      body: JSON.stringify({ tool, arguments: args, confirm: $("toolConfirmToggle").checked, tool_timeout_seconds: buildRuntimeTimeouts().tool_timeout_seconds })
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
    body: JSON.stringify({ text, confirm: $("toolConfirmToggle").checked, stream: false, ...buildRuntimeTimeouts() })
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
  document.body.classList.toggle("sidebar-collapsed", Boolean(state.settings.sidebarCollapsed));
  const theme = deepMerge(DEFAULT_SETTINGS.theme, state.settings.theme || {});
  document.documentElement.style.setProperty("--bg", theme.primary || DEFAULT_SETTINGS.theme.primary);
  document.documentElement.style.setProperty("--accent", theme.accent || DEFAULT_SETTINGS.theme.accent);
  document.documentElement.style.setProperty("--accent-2", theme.accentTwo || DEFAULT_SETTINGS.theme.accentTwo);
  document.documentElement.style.setProperty("--text", theme.text || DEFAULT_SETTINGS.theme.text);
  document.documentElement.style.setProperty("--panel", hexToRgba(theme.panel || DEFAULT_SETTINGS.theme.panel, 0.74));
  document.documentElement.style.setProperty("--panel-strong", hexToRgba(theme.panel || DEFAULT_SETTINGS.theme.panel, 0.92));
  document.documentElement.style.setProperty("--line", hexToRgba(theme.accent || DEFAULT_SETTINGS.theme.accent, 0.13));
  document.documentElement.style.setProperty("--line-strong", hexToRgba(theme.accent || DEFAULT_SETTINGS.theme.accent, 0.25));
  document.documentElement.style.setProperty("--font", fontStack(theme.font));
}

function renderSystemPromptControls() {
  const select = $("settingsPromptSelect");
  if (!select) return;
  select.innerHTML = '<option value="">No system prompt</option>';
  state.systemPrompts.forEach((prompt) => {
    const option = document.createElement("option");
    option.value = prompt.id;
    option.textContent = prompt.title || "Untitled prompt";
    select.appendChild(option);
  });
  select.value = state.activeSystemPromptId || "";
  renderSystemPromptList();
  loadSystemPromptEditor(select.value || null);
}

function renderSystemPromptList() {
  const root = $("systemPromptList");
  if (!root) return;
  if (!state.systemPrompts.length) {
    root.innerHTML = '<div class="prompt-item"><span>No saved prompts yet.</span></div>';
    return;
  }
  root.innerHTML = state.systemPrompts.map((prompt) => `
    <button class="prompt-item ${prompt.id === state.activeSystemPromptId ? "active" : ""}" data-prompt-id="${escapeHtml(prompt.id)}">
      <strong>${escapeHtml(prompt.title || "Untitled prompt")}</strong>
      <span>${escapeHtml(prompt.shortMessage || "No short message")}</span>
    </button>`).join("");
  root.querySelectorAll("[data-prompt-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeSystemPromptId = button.dataset.promptId;
      $("settingsPromptSelect").value = state.activeSystemPromptId;
      loadSystemPromptEditor(state.activeSystemPromptId);
      renderSystemPromptList();
    });
  });
}

function loadSystemPromptEditor(promptId) {
  const prompt = state.systemPrompts.find((candidate) => candidate.id === promptId) || null;
  $("systemPromptTitleInput").value = prompt?.title || "";
  $("systemPromptShortInput").value = prompt?.shortMessage || "";
  $("systemPromptContextInput").value = prompt?.context || "";
  $("settingsSystemPromptInput").value = prompt?.fullPrompt || "";
}

function newSystemPromptDraft() {
  state.activeSystemPromptId = null;
  $("settingsPromptSelect").value = "";
  loadSystemPromptEditor(null);
  $("systemPromptTitleInput").focus();
}

function saveSystemPromptFromEditor() {
  const title = $("systemPromptTitleInput").value.trim() || "Untitled prompt";
  const payload = {
    title,
    shortMessage: $("systemPromptShortInput").value.trim(),
    context: $("systemPromptContextInput").value.trim(),
    fullPrompt: $("settingsSystemPromptInput").value.trim(),
    updatedAt: new Date().toISOString()
  };
  let prompt = state.systemPrompts.find((candidate) => candidate.id === state.activeSystemPromptId);
  if (!prompt) {
    prompt = { id: uid("prompt"), createdAt: new Date().toISOString(), ...payload };
    state.systemPrompts.unshift(prompt);
  } else {
    Object.assign(prompt, payload);
  }
  state.activeSystemPromptId = prompt.id;
  $("systemPromptInput").value = prompt.fullPrompt || "";
  persist();
  renderSystemPromptControls();
}

function deleteActiveSystemPrompt() {
  if (!state.activeSystemPromptId) return;
  state.systemPrompts = state.systemPrompts.filter((prompt) => prompt.id !== state.activeSystemPromptId);
  state.activeSystemPromptId = state.systemPrompts[0]?.id || null;
  $("systemPromptInput").value = activeSystemPrompt()?.fullPrompt || "";
  persist();
  renderSystemPromptControls();
}

async function draftSystemPromptFromSettings() {
  const args = {
    title: $("systemPromptTitleInput").value.trim(),
    short_message: $("systemPromptShortInput").value.trim(),
    context: $("systemPromptContextInput").value.trim(),
    goal: $("settingsSystemPromptInput").value.trim(),
    profile: state.profile
  };
  $("draftSystemPromptBtn").textContent = "Drafting...";
  try {
    const res = await fetch("/api/tool", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tool: "draft_system_prompt", arguments: args, confirm: false, tool_timeout_seconds: buildRuntimeTimeouts().tool_timeout_seconds })
    });
    const data = await res.json();
    const draft = data.tool_call?.data || {};
    if (draft.title) $("systemPromptTitleInput").value = draft.title;
    if (draft.short_message || draft.shortMessage) $("systemPromptShortInput").value = draft.short_message || draft.shortMessage;
    if (draft.context) $("systemPromptContextInput").value = draft.context;
    if (draft.full_prompt || draft.fullPrompt) $("settingsSystemPromptInput").value = draft.full_prompt || draft.fullPrompt;
  } catch (error) {
    $("settingsSystemPromptInput").value = `${$("settingsSystemPromptInput").value}\n\nDraft failed: ${error.message}`.trim();
  } finally {
    $("draftSystemPromptBtn").textContent = "Guided draft";
  }
}

function renderProfileMemoryList() {
  const root = $("profileMemoryList");
  if (!root) return;
  if (!state.memories.length) {
    root.innerHTML = '<div class="memory-item"><span>No memories saved yet.</span></div>';
    return;
  }
  root.innerHTML = state.memories.map((memory) => `<div class="memory-item"><strong>${escapeHtml(memory.title || "Memory")}</strong><span>${escapeHtml(memory.text || "")}</span></div>`).join("");
}

function updateAvatarPreviews() {
  const user = $("profileUserAvatarPreview");
  const assistant = $("profileAssistantAvatarPreview");
  if (user) {
    if (state.profile.userAvatar) user.src = state.profile.userAvatar;
    else user.removeAttribute("src");
  }
  if (assistant) {
    if (state.profile.assistantAvatar) assistant.src = state.profile.assistantAvatar;
    else assistant.removeAttribute("src");
  }
  user?.classList.toggle("empty", !state.profile.userAvatar);
  assistant?.classList.toggle("empty", !state.profile.assistantAvatar);
}

function handleAvatarUpload(kind, file) {
  if (!file) return;
  if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
    openCollectionDetail("Unsupported image", "Use a PNG, JPG, or WebP image for profile icons.", { type: file.type, name: file.name });
    return;
  }
  const reader = new FileReader();
  reader.addEventListener("load", () => {
    if (kind === "user") state.profile.userAvatar = String(reader.result || "");
    else state.profile.assistantAvatar = String(reader.result || "");
    updateAvatarPreviews();
    persist();
    renderChat();
  });
  reader.readAsDataURL(file);
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
  const theme = deepMerge(DEFAULT_SETTINGS.theme, state.settings.theme || {});
  $("themePrimaryColor").value = theme.primary;
  $("themeAccentColor").value = theme.accent;
  $("themeAccentTwoColor").value = theme.accentTwo;
  $("themePanelColor").value = theme.panel;
  $("themeTextColor").value = theme.text;
  $("themeFontSelect").value = theme.font || "system";
  $("settingsMemoryPrefix").value = state.settings.memoryPrefix || DEFAULT_SETTINGS.memoryPrefix;
  $("settingsResponseFormat").value = state.settings.responseFormat || "";
  const opts = state.settings.modelOptions || {};
  const runtimeTimeouts = state.settings.runtimeTimeouts || DEFAULT_SETTINGS.runtimeTimeouts;
  $("settingsOllamaTimeout").value = runtimeTimeouts.ollama ?? DEFAULT_SETTINGS.runtimeTimeouts.ollama;
  $("settingsToolTimeout").value = runtimeTimeouts.tools ?? DEFAULT_SETTINGS.runtimeTimeouts.tools;
  $("settingsTemperature").value = opts.temperature ?? 0.2;
  $("settingsNumCtx").value = opts.num_ctx ?? 4096;
  $("settingsTopP").value = opts.top_p ?? 0.95;
  $("settingsTopK").value = opts.top_k ?? 40;
  $("settingsRepeatPenalty").value = opts.repeat_penalty ?? 1.1;
  $("settingsSeed").value = opts.seed ?? -1;
  $("settingsNumPredict").value = opts.num_predict ?? -1;
  $("settingsKeepAlive").value = opts.keep_alive ?? "";
  $("settingsStopSequences").value = Array.isArray(opts.stop) ? opts.stop.join("\n") : "";
  renderSystemPromptControls();
  $("profileNameInput").value = state.profile.name || "";
  $("profileNicknameInput").value = state.profile.nickname || "";
  $("profileAboutInput").value = state.profile.about || "";
  $("profilePreferencesInput").value = state.profile.preferences || "";
  $("profileOtherInput").value = state.profile.other || "";
  updateAvatarPreviews();
  renderProfileMemoryList();
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
  updateSettingsButtonState();
  $("settingsModelSelect").focus();
}

function closeSettings() {
  $("settingsModal").hidden = true;
  updateSettingsButtonState();
}

function toggleSettings() {
  if ($("settingsModal").hidden) openSettings();
  else closeSettings();
}

function updateSettingsButtonState() {
  const button = $("settingsBtn");
  if (!button) return;
  const isOpen = !$('settingsModal').hidden;
  button.textContent = isOpen ? "Close settings" : "Settings";
  button.title = isOpen ? "Close settings" : "Open settings";
  button.setAttribute("aria-label", button.title);
  button.setAttribute("aria-expanded", String(isOpen));
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
  state.settings.theme = {
    primary: $("themePrimaryColor").value || DEFAULT_SETTINGS.theme.primary,
    accent: $("themeAccentColor").value || DEFAULT_SETTINGS.theme.accent,
    accentTwo: $("themeAccentTwoColor").value || DEFAULT_SETTINGS.theme.accentTwo,
    panel: $("themePanelColor").value || DEFAULT_SETTINGS.theme.panel,
    text: $("themeTextColor").value || DEFAULT_SETTINGS.theme.text,
    font: $("themeFontSelect").value || DEFAULT_SETTINGS.theme.font
  };
  state.settings.memoryPrefix = $("settingsMemoryPrefix").value.trim() || DEFAULT_SETTINGS.memoryPrefix;
  state.settings.responseFormat = $("settingsResponseFormat").value;
  state.settings.runtimeTimeouts = {
    ollama: Math.max(1, Math.min(3600, Number($("settingsOllamaTimeout").value) || DEFAULT_SETTINGS.runtimeTimeouts.ollama)),
    tools: Math.max(1, Math.min(3600, Number($("settingsToolTimeout").value) || DEFAULT_SETTINGS.runtimeTimeouts.tools))
  };
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
  state.activeSystemPromptId = $("settingsPromptSelect").value || null;
  if ($("systemPromptTitleInput").value.trim() || $("settingsSystemPromptInput").value.trim()) saveSystemPromptFromEditor();
  state.profile = {
    name: $("profileNameInput").value.trim(),
    nickname: $("profileNicknameInput").value.trim(),
    about: $("profileAboutInput").value.trim(),
    preferences: $("profilePreferencesInput").value.trim(),
    other: $("profileOtherInput").value.trim(),
    userAvatar: state.profile.userAvatar || "",
    assistantAvatar: state.profile.assistantAvatar || ""
  };
  $("systemPromptInput").value = activeSystemPrompt()?.fullPrompt || "";
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
    ["Tool calls", (message.toolCalls || []).length],
    ["Sources", collectSources(message).length],
    ["Variant", `${(message.activeVariant || 0) + 1} of ${message.variants?.length || 1}`]
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
  const profile = activeModelProfiles().find((item) => item.model === modelName) || null;
  const live = state.models.find((item) => item.name === modelName || item.model === modelName) || null;
  const payload = { selected: modelName || "auto", profile, live, model_options: buildModelOptions(), response_format: buildResponseFormat() };
  openDetailModal({
    eyebrow: "Model",
    title: modelName || "Auto route",
    html: `${detailTable([
      ["Selected", modelName || "Auto route"],
      ["Profile", profile?.category || "server-side / live"],
      ["Job", profile?.job || "not mapped"],
      ["Benchmark score", profile?.benchmark_score || live?.benchmark?.overall_score || "not benchmarked"],
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
      ["Stability", doc.stability || "experimental"],
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
  $("settingsBtn").addEventListener("click", toggleSettings);
  $("closeSettingsBtn").addEventListener("click", closeSettings);
  $("cancelSettingsBtn").addEventListener("click", closeSettings);
  $("saveSettingsBtn").addEventListener("click", saveSettings);
  document.querySelectorAll(".settings-tab").forEach((button) => button.addEventListener("click", () => switchSettingsTab(button.dataset.settingsTab)));
  $("settingsClearJournalBtn").addEventListener("click", () => { closeSettings(); requestClearJournal(); });
  $("settingsDeleteAllSessionsBtn")?.addEventListener("click", () => { closeSettings(); requestDeleteAllSessions(); });
  $("settingsExportActiveBtn")?.addEventListener("click", exportSession);
  $("settingsClearChatBtn")?.addEventListener("click", () => { closeSettings(); clearActiveSession(); });
  $("settingsExportAllBtn").addEventListener("click", exportAllSessions);
  $("settingsPromptSelect")?.addEventListener("change", (event) => {
    state.activeSystemPromptId = event.target.value || null;
    $("systemPromptInput").value = activeSystemPrompt()?.fullPrompt || "";
    loadSystemPromptEditor(state.activeSystemPromptId);
    renderSystemPromptList();
  });
  $("newSystemPromptBtn")?.addEventListener("click", newSystemPromptDraft);
  $("saveSystemPromptBtn")?.addEventListener("click", saveSystemPromptFromEditor);
  $("deleteSystemPromptBtn")?.addEventListener("click", deleteActiveSystemPrompt);
  $("draftSystemPromptBtn")?.addEventListener("click", draftSystemPromptFromSettings);
  $("profileUserAvatarInput")?.addEventListener("change", (event) => handleAvatarUpload("user", event.target.files?.[0]));
  $("profileAssistantAvatarInput")?.addEventListener("change", (event) => handleAvatarUpload("assistant", event.target.files?.[0]));
  ["themePrimaryColor", "themeAccentColor", "themeAccentTwoColor", "themePanelColor", "themeTextColor", "themeFontSelect"].forEach((id) => {
    $(id)?.addEventListener("input", () => {
      state.settings.theme = {
        primary: $("themePrimaryColor").value,
        accent: $("themeAccentColor").value,
        accentTwo: $("themeAccentTwoColor").value,
        panel: $("themePanelColor").value,
        text: $("themeTextColor").value,
        font: $("themeFontSelect").value
      };
      applySettingsVisuals();
    });
  });
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
  $("closeRetryBtn").addEventListener("click", closeRetryDialog);
  $("cancelRetryBtn").addEventListener("click", closeRetryDialog);
  $("runRetryBtn").addEventListener("click", runRetryFromDialog);
  $("retryDialog").addEventListener("click", (event) => { if (event.target.id === "retryDialog") closeRetryDialog(); });
  $("closeDetailBtn").addEventListener("click", closeDetailModal);
  $("detailCloseBtn").addEventListener("click", closeDetailModal);
  $("detailModal").addEventListener("click", (event) => { if (event.target.id === "detailModal") closeDetailModal(); });
  $("detailCopyBtn").addEventListener("click", async () => {
    await navigator.clipboard.writeText(JSON.stringify(state.detailPayload || {}, null, 2));
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    if (!$("confirmDialog").hidden) closeConfirmDialog();
    else if (!$("retryDialog").hidden) closeRetryDialog();
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
  downloadJson("showcase-ui-sessions.json", { exportedAt: new Date().toISOString(), sessions: state.sessions, memories: state.memories, settings: state.settings, systemPrompts: state.systemPrompts, activeSystemPromptId: state.activeSystemPromptId, profile: state.profile });
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
  state.systemPrompts = [];
  state.activeSystemPromptId = null;
  state.profile = structuredClone(DEFAULT_PROFILE);
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
  $("brandCard").addEventListener("click", () => openCollectionDetail("Local LLM Tooling Showcase", "A local-first tool-aware Ollama cockpit with chat, tools, adapters, journal, model settings, benchmarked profiles, and memory support.", { version: "ui-v5-benchmarks", models: state.models.length, benchmarked_profiles: state.benchmarkProfiles.length, tools: state.tools.length, adapters: state.adapters.length }));
  $("modelPanel").addEventListener("dblclick", () => openModelDetail($("modelSelect").value));
  $("sessionsPanel").addEventListener("dblclick", () => openSessionDetail(activeSession()));
  $("memoriesPanel").addEventListener("dblclick", () => openCollectionDetail("Memories", `${state.memories.length} local browser memories.`, state.memories));
  $("sessionHeader").addEventListener("dblclick", () => openSessionDetail(activeSession()));
  $("toolsPanel").addEventListener("dblclick", () => openCollectionDetail("Tools", `${state.tools.length} available tools.`, { tools: state.tools, tool_cards: state.toolCards }));
  $("adaptersPanel").addEventListener("dblclick", () => openCollectionDetail("Adapters", `${state.adapters.length} workspace adapters loaded.`, state.adapters));
  $("journalPanel").addEventListener("dblclick", openJournalSummaryDetail);
  $("overviewPanel")?.addEventListener("dblclick", () => openCollectionDetail("Overview", "Full local runtime overview.", { readiness: runtimeReadiness(), sessions: state.sessions.length, tools: state.tools.length, adapters: state.adapters.length, journal: state.journalStats }));
  $("composerPanel").addEventListener("dblclick", () => openCollectionDetail("Composer", "Prompt composer details and current request options.", { model: $("modelSelect").value || "auto", options: buildModelOptions(), system_prompt_chars: $("systemPromptInput").value.length }));
  $("runtimeStatusStrip")?.addEventListener("click", () => openCollectionDetail("Runtime readiness", "Current local runtime health and setup signals.", { readiness: runtimeReadiness(), runtime: state.runtime, models: state.models.length, tools: state.tools.length, adapters: state.adapters.length, journal: state.journalStats }));
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
  $("modelSelect").addEventListener("change", () => { updateModelMeta(); renderRuntimeStatus(); persist(); });
  $("toolSelect").addEventListener("change", updateToolExample);
  $("runToolBtn").addEventListener("click", runManualTool);
  $("runAutonomousBtn").addEventListener("click", runAutonomous);
  $("newSessionBtn").addEventListener("click", () => createSession(true));
  $("sidebarNewChatBtn")?.addEventListener("click", (event) => { event.stopPropagation(); createSession(true); });
  $("sidebarSearchBtn")?.addEventListener("click", (event) => { event.stopPropagation(); searchSessions(); });
  $("recentsToggleBtn")?.addEventListener("click", (event) => { event.stopPropagation(); toggleRecentSessionsPullout(); });
  $("sidebarCollapseBtn")?.addEventListener("click", (event) => { event.stopPropagation(); toggleSidebarCollapsed(); });
  $("addMemoryBtn").addEventListener("click", addMemory);
  $("clearBtn")?.addEventListener("click", clearActiveSession);
  $("refreshAdaptersBtn").addEventListener("click", loadAdapters);
  $("refreshJournalBtn").addEventListener("click", loadJournal);
  $("clearJournalBtn").addEventListener("click", requestClearJournal);
  $("systemPromptBtn")?.addEventListener("click", () => {
    const box = $("systemPromptInput");
    box.hidden = !box.hidden;
    if (!box.hidden) box.focus();
  });
  $("densityBtn")?.addEventListener("click", () => {
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
  await Promise.allSettled([loadModels(), loadTools(), loadAdapters(), loadJournal(), loadRuntime()]);
  renderAll();
}

boot();
