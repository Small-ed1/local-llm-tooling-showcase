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

const THEME_COLOR_FIELDS = [
  { key: "primary", label: "Primary background", fallback: "#07100d" },
  { key: "backgroundSoft", label: "Secondary background", fallback: "#0b1712" },
  { key: "backgroundStart", label: "Gradient start", fallback: "#050807" },
  { key: "backgroundEnd", label: "Gradient end", fallback: "#020403" },
  { key: "backgroundGlow", label: "Background glow", fallback: "#78f0ad" },
  { key: "backgroundGlowTwo", label: "Background glow 2", fallback: "#529f7b" },
  { key: "panel", label: "Panel", fallback: "#13261e" },
  { key: "panelStrong", label: "Strong panel", fallback: "#162b22" },
  { key: "surface", label: "Surface tint", fallback: "#ffffff" },
  { key: "surfaceDark", label: "Dark surface tint", fallback: "#000000" },
  { key: "input", label: "Input background", fallback: "#020604" },
  { key: "text", label: "Main text", fallback: "#edf7f1" },
  { key: "muted", label: "Muted text", fallback: "#91a89c" },
  { key: "mutedTwo", label: "Faint text", fallback: "#647a70" },
  { key: "accent", label: "Accent", fallback: "#78f0ad" },
  { key: "accentTwo", label: "Accent 2", fallback: "#b6ffd2" },
  { key: "accentContrast", label: "Accent text", fallback: "#04100a" },
  { key: "line", label: "Border", fallback: "#a4ffca" },
  { key: "lineStrong", label: "Strong border", fallback: "#a4ffca" },
  { key: "warn", label: "Warning", fallback: "#ffd166" },
  { key: "bad", label: "Danger", fallback: "#ff6b6b" },
  { key: "badText", label: "Danger text", fallback: "#ffaaaa" },
  { key: "ok", label: "Success", fallback: "#7bffa7" },
  { key: "codeText", label: "Code text", fallback: "#d9fbe7" },
  { key: "thinkingText", label: "Thinking text", fallback: "#e4d6a8" },
  { key: "shadow", label: "Shadow", fallback: "#000000" },
  { key: "grid", label: "Grid lines", fallback: "#ffffff" },
  { key: "overlay", label: "Overlay", fallback: "#000000" },
  { key: "userAvatar", label: "User avatar", fallback: "#b0ffd2" }
];

const DEFAULT_THEME = Object.fromEntries(THEME_COLOR_FIELDS.map((field) => [field.key, field.fallback]));
DEFAULT_THEME.font = "system";

const THEME_PRESETS = {
  forest: { label: "Forest cockpit", ...DEFAULT_THEME },
  midnight: {
    label: "Midnight blue",
    ...DEFAULT_THEME,
    primary: "#070b18",
    backgroundSoft: "#10182a",
    backgroundStart: "#030613",
    backgroundEnd: "#01030a",
    backgroundGlow: "#82aaff",
    backgroundGlowTwo: "#536dfe",
    panel: "#111827",
    panelStrong: "#1b2740",
    input: "#050916",
    text: "#eef4ff",
    muted: "#9aa8c7",
    mutedTwo: "#6f7c99",
    accent: "#82aaff",
    accentTwo: "#c3dafe",
    line: "#9bbcff",
    lineStrong: "#c3dafe",
    codeText: "#dce8ff",
    thinkingText: "#d7cffd"
  },
  paper: {
    label: "Warm paper",
    ...DEFAULT_THEME,
    primary: "#18120b",
    backgroundSoft: "#24180e",
    backgroundStart: "#100a05",
    backgroundEnd: "#050302",
    backgroundGlow: "#f2b35d",
    backgroundGlowTwo: "#a97135",
    panel: "#2b2118",
    panelStrong: "#3a2b1d",
    input: "#160f08",
    text: "#fff7e8",
    muted: "#c9ad8c",
    mutedTwo: "#8d7459",
    accent: "#f2b35d",
    accentTwo: "#ffe5b4",
    line: "#f0c989",
    lineStrong: "#ffe5b4",
    accentContrast: "#1a1007",
    warn: "#ffd166",
    codeText: "#ffe8bd",
    thinkingText: "#f7d69d",
    font: "serif"
  },
  mono: {
    label: "Terminal mono",
    ...DEFAULT_THEME,
    primary: "#050505",
    backgroundSoft: "#0b0b0b",
    backgroundStart: "#000000",
    backgroundEnd: "#000000",
    backgroundGlow: "#00ff88",
    backgroundGlowTwo: "#008f5d",
    panel: "#111111",
    panelStrong: "#191919",
    input: "#020202",
    text: "#effff5",
    muted: "#92bfa8",
    mutedTwo: "#668270",
    accent: "#00ff88",
    accentTwo: "#bcffd9",
    line: "#58ffa8",
    lineStrong: "#bcffd9",
    accentContrast: "#001b0d",
    ok: "#00ff88",
    codeText: "#bcffd9",
    font: "mono"
  }
};

const SYSTEM_PROMPT_PRESETS = [
  { title: "Clean everyday assistant", shortMessage: "Helpful, concise, non-technical by default", context: "Use simple language. Hide implementation details unless asked.", fullPrompt: "You are a clear, friendly local assistant. Answer directly, keep formatting readable, and avoid exposing internal tool or JSON details unless the user asks for debugging information." },
  { title: "Senior software engineer", shortMessage: "Direct coding help", context: "Use tools when code or local files matter.", fullPrompt: "You are a pragmatic senior software engineer. Inspect the codebase before assuming, make minimal correct changes, explain tradeoffs briefly, and verify changes when practical." },
  { title: "Research analyst", shortMessage: "Careful evidence-first analysis", context: "Prefer sources and structured conclusions.", fullPrompt: "You are a careful research analyst. Separate facts from assumptions, cite source context when tools are used, and end with clear recommendations or next steps." },
  { title: "Linux troubleshooter", shortMessage: "Stepwise local diagnostics", context: "Focus on reproducible commands and safety.", fullPrompt: "You are a Linux troubleshooting assistant. Ask for or inspect exact errors, prefer safe read-only diagnostics first, and explain command purpose before risky operations." }
];

const MODEL_NUMERIC_OPTION_KEYS = [
  "num_keep", "seed", "num_predict", "top_k", "top_p", "min_p", "typical_p", "repeat_last_n", "temperature", "repeat_penalty", "presence_penalty", "frequency_penalty", "num_ctx", "num_batch", "num_gpu", "main_gpu", "num_thread"
];
const MODEL_BOOLEAN_OPTION_KEYS = ["penalize_newline", "numa", "use_mmap"];

const MODEL_OPTION_GROUPS = {
  modelGenerationGrid: ["num_keep", "seed", "num_predict"],
  modelSamplingGrid: ["top_k", "top_p", "min_p", "typical_p", "repeat_last_n", "temperature", "repeat_penalty", "presence_penalty", "frequency_penalty"],
  modelRuntimeGrid: ["num_ctx", "num_batch", "num_gpu", "main_gpu", "num_thread"],
  modelBooleanGrid: MODEL_BOOLEAN_OPTION_KEYS
};

const MODEL_OPTION_LABELS = {
  num_keep: "Num keep", num_predict: "Max prediction", top_k: "Top K", top_p: "Top P", min_p: "Min P", typical_p: "Typical P", repeat_last_n: "Repeat last N", repeat_penalty: "Repeat penalty", presence_penalty: "Presence penalty", frequency_penalty: "Frequency penalty", penalize_newline: "Penalize newline", num_ctx: "Context tokens", num_batch: "Batch size", num_gpu: "GPU layers", main_gpu: "Main GPU", num_thread: "Threads", use_mmap: "Use mmap"
};

const HELP_TOPICS = [
  {
    id: "quickstart",
    title: "Quickstart",
    summary: "Install, start the server, open the browser UI, and run the first smoke checks.",
    sections: [
      {
        title: "What this project is",
        body: [
          "Local LLM Tooling Showcase is a local-first assistant runtime. It is meant to show how chat, deterministic routing, guarded tools, local Ollama models, workspace inspection, model benchmarks, and event logging fit together in one compact project.",
          "It is not a hosted SaaS app and it is not a full sandbox. It runs on your machine, reads from the workspace you point it at, and keeps risky local actions behind explicit boundaries."
        ]
      },
      {
        title: "Normal startup flow",
        body: [
          "Clone the repo, install the package, start the web server, and open the browser UI at the local address. The default web server binds to loopback, so it is intended for your own machine unless you intentionally pass a wider host.",
          "Once the page opens, confirm the runtime status, make sure the model selector is populated if you want Ollama-backed answers, and send a basic prompt. If Ollama is not running, deterministic local tool routes can still work, but open-ended model replies will fail clearly instead of pretending everything is fine."
        ]
      },
      {
        title: "What to verify first",
        body: [
          "Check that the Python package installed, the static assets load, the server responds, and Ollama is reachable if you want model-backed responses. If the model list is empty, check Ollama before debugging the UI.",
          "For frontend changes, this project has no build step. Use a JavaScript syntax check and then do a manual browser smoke test."
        ]
      }
    ],
    checklist: [
      "Run the installer for your OS.",
      "Start the server with tooling-showcase serve.",
      "Open http://127.0.0.1:8123.",
      "Check the runtime status area.",
      "Send a simple prompt.",
      "Try a deterministic local request like reading or finding README.",
      "Run doctor if anything feels off."
    ],
    commands: [
      "./install.sh",
      "tooling-showcase serve",
      "tooling-showcase serve --host 127.0.0.1 --port 8123",
      "tooling-showcase doctor",
      "node --check src/tooling_showcase/static/app.js"
    ]
  },
  {
    id: "windows",
    title: "Windows Setup",
    summary: "PowerShell setup, virtualenv activation, windows-curses, and common Windows install issues.",
    sections: [
      {
        title: "Use the Windows installer",
        body: [
          "Windows should use the PowerShell installer instead of the Unix shell installer. The Windows script creates or reuses a virtual environment, upgrades pip, installs windows-curses, installs pytest, installs the project in editable mode, and then starts the server.",
          "The curses compatibility package matters because Python's built-in curses module is not available by default on Windows."
        ]
      },
      {
        title: "Folder expectation",
        body: [
          "The current Windows installer expects the project folder at $HOME\\Projects\\local-llm-tooling-showcase. If the repo is somewhere else, either move it there or edit the ProjectPath variable at the top of the script.",
          "Run the script from PowerShell. If execution policy blocks it, use the bypass command shown below."
        ]
      },
      {
        title: "Common Windows failures",
        body: [
          "If you see ModuleNotFoundError for curses or _curses, activate the virtual environment and install windows-curses inside it.",
          "If py -3.11 fails, install Python 3.11 or adjust the script to use the Python launcher version you actually have. If tooling-showcase is not found after install, reactivate the virtual environment and rerun python -m pip install -e ."
        ]
      }
    ],
    checklist: [
      "Use install-windows.ps1, not install.sh.",
      "Confirm Python 3.11 is installed.",
      "Confirm the repo path matches the script path.",
      "Install windows-curses inside the venv.",
      "Start Ollama separately if you want model-backed responses."
    ],
    commands: [
      "powershell -ExecutionPolicy Bypass -File .\\install-windows.ps1",
      "py -3.11 -m venv .venv",
      ".\\.venv\\Scripts\\Activate.ps1",
      "python -m pip install windows-curses pytest",
      "python -m pip install -e .",
      "tooling-showcase serve"
    ]
  },
  {
    id: "ollama",
    title: "Ollama and Models",
    summary: "Model inventory, routing profiles, thinking mode, timeouts, and slow response causes.",
    sections: [
      {
        title: "How Ollama fits in",
        body: [
          "The backend uses Ollama for open-ended model responses. Requests can include a selected model, system prompt, response format, streaming, model options, and timeout settings.",
          "If Ollama is disabled or unreachable, deterministic local tool routes can still work, but general LLM fallback will report failure instead of silently inventing an answer."
        ]
      },
      {
        title: "Model routing",
        body: [
          "The app can route requests by category and can use local benchmark profiles when they exist. Benchmarking helps assign installed models to jobs like general chat, coding, reasoning, summary, fast responses, Linux help, or other categories.",
          "If no benchmark profile exists, models are treated as unprofiled and the UI should encourage running the benchmark suite."
        ]
      },
      {
        title: "Thinking mode and options",
        body: [
          "The UI exposes model options such as temperature, context tokens, batch size, GPU layers, repeat penalty, top-p, top-k, num_predict, seed, and related sampling/runtime values.",
          "Thinking mode is only useful for models that support it. If a model rejects thinking, the Ollama client can retry without thinking rather than failing the whole request."
        ]
      },
      {
        title: "Why responses get slow",
        body: [
          "Large models, high context size, high max prediction, cold model loads, CPU-only inference, and too many tool/model loop steps can all make responses feel slow.",
          "Start with a tiny benchmark smoke run, then expand to full benchmarking once the basic server and Ollama path work."
        ]
      }
    ],
    checklist: [
      "Run ollama list.",
      "Make sure Ollama is serving locally.",
      "Check the model selector.",
      "Run benchmark --list-models.",
      "Run a small benchmark before a full benchmark.",
      "Reduce num_ctx or num_predict if responses stall."
    ],
    commands: [
      "ollama serve",
      "ollama list",
      "tooling-showcase models",
      "tooling-showcase benchmark --list-models",
      "tooling-showcase benchmark --limit-tasks 2",
      "tooling-showcase benchmark --all"
    ]
  },
  {
    id: "chat",
    title: "Chat Workflow",
    summary: "User mode, developer mode, message editing, retries, sessions, and normal prompting.",
    sections: [
      {
        title: "User mode vs developer mode",
        body: [
          "User mode keeps the interface focused on normal chatting. Developer mode exposes the manual tool console, journal, raw-ish diagnostics, and deeper runtime controls.",
          "Tools and Journal should not appear in the sidebar while in user mode. If they do, the dev-only nav patch has not been applied correctly."
        ]
      },
      {
        title: "Chat-first behavior",
        body: [
          "The intended experience is natural language first. The user should ask normal questions, and the backend decides whether a deterministic route, direct model answer, contextual tool call, or model-directed tool loop is appropriate.",
          "The model should not dump raw tool orchestration unless traces are explicitly enabled. Tool use should stay behind the curtain unless it improves clarity."
        ]
      },
      {
        title: "Editing and retrying",
        body: [
          "Message variants let you retry an assistant response without losing the original. Editing a previous user prompt should branch the conversation from that point so you can compare answers without starting from scratch.",
          "This is useful for demos because it shows that the runtime can preserve local state while still letting the user iterate."
        ]
      },
      {
        title: "Good first prompts",
        body: [
          "Start with simple local workspace tasks: ask it to look around the project, find README, summarize a file, search content, or explain available tools.",
          "Then test harder requests such as comparing project structure, finding where an API route lives, or asking for a release-readiness checklist."
        ]
      }
    ],
    checklist: [
      "Use user mode for a clean demo.",
      "Use developer mode when debugging tools or events.",
      "Retry a response to confirm variants work.",
      "Edit a user prompt to confirm branching works.",
      "Archive old chats instead of deleting them during demos."
    ],
    commands: [
      "Ask: look around this project",
      "Ask: summarize README.md",
      "Ask: search content ToolRuntime",
      "Ask: what tools are available?",
      "Ask: remember that I prefer concise answers"
    ]
  },
  {
    id: "tools",
    title: "Tools and Safety",
    summary: "Planner-safe tools, manual tools, confirmation gates, shell safety, and local file boundaries.",
    sections: [
      {
        title: "Tool layers",
        body: [
          "The project has a broad ToolRuntime, but the model planner should only receive the smaller planner-safe tool surface. This keeps experimental or risky tools away from normal model-directed tool calls.",
          "Manual tool execution is for developer/debug use. Normal users should be able to stay in chat and let the backend choose tools when useful."
        ]
      },
      {
        title: "Safe automatic tools",
        body: [
          "Read-only and planner-safe tools can run automatically when they improve correctness. These include file search, file read, content search, tree view, index query, library search, web lookup, and memory operations where appropriate.",
          "The backend validates tool names and normalizes arguments. If the model invents a tool name, the request is rejected instead of executing unknown behavior."
        ]
      },
      {
        title: "Shell and risky actions",
        body: [
          "Shell execution is guarded. Some blocked substrings should never run, and risky operations require confirmation when the policy says so.",
          "This matters because the project is local-first, not a sandbox. Treat the workspace as real files on a real machine."
        ]
      },
      {
        title: "When to inspect tools manually",
        body: [
          "Use the manual tool console when debugging route behavior, checking JSON argument shapes, confirming tool output, or demonstrating what the runtime can reach.",
          "For normal usage, prefer asking in chat. If the chat result seems wrong, switch to developer mode and check the journal or manual tool output."
        ]
      }
    ],
    checklist: [
      "Keep risky tools confirmation-gated.",
      "Do not expose the full runtime tool list to model planning.",
      "Use tree_view before deep repo questions.",
      "Use file_search before read_file unless the path is exact.",
      "Use content_search for symbols, routes, and function names.",
      "Use shell_command only for explicit local terminal tasks."
    ],
    commands: [
      "tooling-showcase ask \"find file README\"",
      "tooling-showcase ask \"read file README.md\"",
      "tooling-showcase ask \"search content ToolRuntime\"",
      "tooling-showcase ask --confirm \"run git status\"",
      "tooling-showcase doctor --json"
    ]
  },
  {
    id: "runtime",
    title: "Runtime and API",
    summary: "Server routes, static files, journal, models, adapters, and the Ollama-compatible wrapper.",
    sections: [
      {
        title: "Web server routes",
        body: [
          "The stdlib server serves index.html at / and /index.html, static files under /static/, and JSON endpoints for journal, adapters, tools, models, runtime, and manual tool calls.",
          "That means opening index.html directly from the filesystem is not equivalent to running the app. The UI expects backend API routes to exist."
        ]
      },
      {
        title: "Main API behavior",
        body: [
          "The main chat endpoint accepts message text, confirmation settings, selected model, system prompt, streaming, model options, response format, and timeout overrides.",
          "The frontend should treat the backend as the source of truth for available tools, runtime status, model inventory, and journal records."
        ]
      },
      {
        title: "Ollama-compatible wrapper",
        body: [
          "The wrapper exposes familiar Ollama-shaped /api/chat and /api/generate endpoints while routing through the showcase service underneath.",
          "Use the wrapper when you want another local client to talk to this project as if it were an Ollama-compatible endpoint, but with showcase tools and routing available."
        ]
      }
    ],
    checklist: [
      "Serve through tooling-showcase serve, not file://.",
      "Check /api/runtime when the UI status looks wrong.",
      "Check /api/models when the model selector is empty.",
      "Use serve-ollama only when you need Ollama API compatibility.",
      "Keep default bind host as 127.0.0.1 unless LAN access is intentional."
    ],
    commands: [
      "tooling-showcase serve",
      "tooling-showcase serve --host 127.0.0.1 --port 8123",
      "tooling-showcase serve-ollama --port 11436",
      "curl http://127.0.0.1:8123/api/runtime",
      "curl http://127.0.0.1:8123/api/models"
    ]
  },
  {
    id: "data",
    title: "Sessions, Memory, and State",
    summary: "Browser-local UI state, backend state files, exports, archives, memories, and resets.",
    sections: [
      {
        title: "Where state lives",
        body: [
          "Browser sessions, UI settings, system prompts, profile fields, avatars, and UI memories live in browser local storage.",
          "Backend memories, benchmark results, event journals, logs, indexes, and tool stats live under ignored state files in the project state area."
        ]
      },
      {
        title: "Sessions and archive",
        body: [
          "Archive should hide old chats from normal history without deleting them. This is safer during demos because you can clean up the sidebar without destroying useful examples.",
          "Deletion should remain more deliberate than archive. If the UI gets weird, export first, then clear state."
        ]
      },
      {
        title: "Memories",
        body: [
          "Memories should be stable preferences or reusable details, not secrets, passwords, one-time prompt text, or random temporary notes.",
          "The user should stay in control of memory creation, editing, export, and deletion."
        ]
      },
      {
        title: "Import and export",
        body: [
          "System prompts, profile data, and memories can be portable if exported as JSON or simple text-like files.",
          "A good import flow should accept JSON arrays/objects where possible and treat text files as a single imported item using the filename as a title."
        ]
      }
    ],
    checklist: [
      "Export sessions before clearing browser storage.",
      "Archive before deleting.",
      "Keep memories stable and non-secret.",
      "Use JSON exports for portability.",
      "Reset browser state only after saving anything important."
    ],
    commands: [
      "Settings -> Data -> Export all sessions",
      "Settings -> Memory -> Export memories",
      "Settings -> System prompts -> Export",
      "Settings -> Data -> Clear browser state",
      "tooling-showcase journal --limit 5"
    ]
  },
  {
    id: "settings",
    title: "Settings and Personalization",
    summary: "Mode, density, streaming, confirmations, system prompts, profile, avatars, themes, and model options.",
    sections: [
      {
        title: "Core settings",
        body: [
          "Mode controls whether the interface behaves like a clean user-facing chat app or a developer/debug cockpit. Density controls spacing. Streaming controls whether responses arrive incrementally.",
          "Confirmation settings matter for risky tool calls. Keep confirmations enabled when demonstrating shell-like actions."
        ]
      },
      {
        title: "System prompts",
        body: [
          "System prompt presets let you create reusable behavior profiles. A good preset has a clear title, short message, context note, and full prompt.",
          "The active system prompt should shape response style without leaking internal runtime details to the user."
        ]
      },
      {
        title: "Profile and avatars",
        body: [
          "The profile area is for local personalization. Avatar uploads are stored in browser-local state, so clearing browser storage can remove them.",
          "Use small PNG, JPG, or WebP images to avoid bloating local storage."
        ]
      },
      {
        title: "Model options",
        body: [
          "The model option grids expose generation, sampling, runtime, and boolean settings. These can strongly affect speed, repetition, creativity, and memory use.",
          "For demos, start conservative: moderate context, low temperature, default GPU settings, and no extreme max prediction unless you need long answers."
        ]
      }
    ],
    checklist: [
      "Use user mode for normal demos.",
      "Use developer mode for debugging.",
      "Keep temperature low for technical checks.",
      "Use theme presets before manually editing colors.",
      "Export system prompts before resetting state."
    ],
    commands: [
      "Settings -> General -> Mode",
      "Settings -> System prompts -> Guided draft",
      "Settings -> Profile -> Avatar upload",
      "Settings -> Models -> Context tokens",
      "Settings -> Theme -> Forest cockpit"
    ]
  },
  {
    id: "troubleshooting",
    title: "Troubleshooting",
    summary: "Ollama failures, empty model selector, static file issues, broken layouts, tool errors, and validation checks.",
    sections: [
      {
        title: "The page loads but nothing works",
        body: [
          "Make sure you are serving the app through tooling-showcase serve. Opening index.html directly will not provide /api/runtime, /api/models, /api/ask, or the static route behavior the frontend expects.",
          "Check the browser network tab for missing /static/app.css, /static/app.js, or failed API routes."
        ]
      },
      {
        title: "The model selector is empty",
        body: [
          "Check whether Ollama is installed and serving. Then run ollama list. If the backend can reach Ollama but models are missing, install or pull a model.",
          "Run tooling-showcase models and benchmark --list-models to compare what the CLI sees against what the browser shows."
        ]
      },
      {
        title: "Streaming stalls or feels slow",
        body: [
          "Increase the Ollama timeout, reduce context size, reduce max prediction, or choose a smaller model. Cold model loading can make the first response much slower than later responses.",
          "If a tool call is involved, also check the tool timeout and journal."
        ]
      },
      {
        title: "Tool output seems wrong",
        body: [
          "Switch to developer mode, inspect the journal, and try the same tool manually with explicit JSON arguments.",
          "If the planner picked the wrong tool, improve the tool decision prompt or deterministic route. If the tool returned bad data, fix the tool implementation or its argument normalization."
        ]
      },
      {
        title: "Frontend changes broke the UI",
        body: [
          "Run node --check on app.js first. Then smoke test the page manually. This project has no frontend build step, so syntax checks and browser testing matter more.",
          "If CSS behaves strangely, look for duplicate breakpoint rules, stale old stylesheets, and hidden elements that are still taking layout space."
        ]
      }
    ],
    checklist: [
      "Run tooling-showcase doctor.",
      "Run node --check on app.js.",
      "Check missing static files in browser devtools.",
      "Check /api/runtime.",
      "Check Ollama with ollama list.",
      "Inspect the journal in developer mode.",
      "Export state before clearing browser storage."
    ],
    commands: [
      "tooling-showcase doctor",
      "tooling-showcase doctor --json",
      "node --check src/tooling_showcase/static/app.js",
      "pytest tests/",
      "git diff --check",
      "ollama list",
      "tooling-showcase journal --limit 20"
    ]
  }
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
  mode: "dev",
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
  sessionSearchQuery: "",
  deepResearch: {
    mode: "local",
    depth: 2
  },
  runtimeTimeouts: {
    ollama: 120,
    tools: 30
  },
  theme: { ...DEFAULT_THEME },
  modelOptions: {
    num_keep: -1,
    temperature: 0.2,
    num_ctx: 4096,
    num_batch: 256,
    num_gpu: -1,
    main_gpu: 0,
    num_thread: 10,
    top_p: 0.95,
    top_k: 40,
    min_p: 0,
    typical_p: 1,
    repeat_penalty: 1.1,
    repeat_last_n: 64,
    presence_penalty: 0,
    frequency_penalty: 0,
    penalize_newline: true,
    numa: false,
    use_mmap: true,
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
  journal: {
    eyebrow: "Observability",
    title: "Journal",
    summary: "Review backend events, tool calls, and autonomous-run traces."
  },
  help: {
    eyebrow: "Help",
    title: "Help and troubleshooting",
    summary: "Read comprehensive setup, troubleshooting, import/export, and operating guides."
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

const LEGACY_STORAGE_KEYS = [
  "showcase.ui.sessions.v1",
  "showcase.ui.sessions.v2",
  "showcase.ui.activeSession.v1",
  "showcase.ui.activeSession.v2",
  "showcase.ui.memories.v1",
  "showcase.ui.memories.v2",
  "showcase.ui.settings.v1",
  "showcase.ui.settings.v2",
  "showcase.ui.systemPrompt.v1",
  "showcase.ui.systemPrompt.v2"
];

const MAX_SETTINGS_TEXT_CHARS = 12000;
const MAX_PREFIX_CHARS = 600;
const MAX_PROFILE_TEXT_CHARS = 8000;
const MAX_AVATAR_DIMENSION = 192;
const MAX_AVATAR_DATA_URL_CHARS = 220000;

const LOCAL_STORAGE_SCHEMA_VERSION = 3;
const CHAT_CONTEXT_MAX_MESSAGES = 24;
const CHAT_CONTEXT_MAX_CHARS = 24000;


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
  composerDeepResearch: false,
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

function themeFieldDefault(key) {
  return THEME_COLOR_FIELDS.find((field) => field.key === key)?.fallback || "#13261e";
}

function normalizeHex(hex, fallback = "#13261e") {
  const fallbackClean = String(fallback || "#13261e").replace("#", "");
  const cleanFallback = /^[0-9a-f]{6}$/i.test(fallbackClean) ? fallbackClean : "13261e";
  const clean = String(hex || "").replace("#", "");
  return `#${/^[0-9a-f]{6}$/i.test(clean) ? clean : cleanFallback}`;
}

function hexToRgba(hex, alpha = 1, fallback = "#13261e") {
  const clean = normalizeHex(hex, fallback).replace("#", "");
  const value = Number.parseInt(clean, 16);
  const r = (value >> 16) & 255;
  const g = (value >> 8) & 255;
  const b = value & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function normalizeTheme(theme = {}) {
  const next = { ...DEFAULT_THEME, ...(theme || {}) };
  THEME_COLOR_FIELDS.forEach((field) => {
    next[field.key] = normalizeHex(next[field.key], field.fallback);
  });
  next.font = next.font || DEFAULT_THEME.font;
  return next;
}

function setThemeHexVar(name, theme, key) {
  document.documentElement.style.setProperty(name, normalizeHex(theme[key], themeFieldDefault(key)));
}

function setThemeRgbaVar(name, theme, key, alpha) {
  document.documentElement.style.setProperty(name, hexToRgba(theme[key], alpha, themeFieldDefault(key)));
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
  return state.sessions.find((session) => session.id === state.activeSessionId) ?? state.sessions.find((session) => !session.archived) ?? state.sessions[0];
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

function boundedString(value, fallback = "", maxChars = MAX_SETTINGS_TEXT_CHARS) {
  const text = String(value ?? fallback ?? "");
  return text.length > maxChars ? text.slice(0, maxChars) : text;
}

function boundedNumber(value, fallback, min = -Infinity, max = Infinity) {
  const number = Number(value);
  const safe = Number.isFinite(number) ? number : fallback;
  return Math.max(min, Math.min(max, safe));
}

function sanitizeSettings(rawSettings = {}) {
  const raw = rawSettings && typeof rawSettings === "object" ? rawSettings : {};
  const merged = deepMerge(DEFAULT_SETTINGS, raw);
  const sanitized = {
    mode: ["user", "dev"].includes(merged.mode) ? merged.mode : DEFAULT_SETTINGS.mode,
    density: ["comfortable", "compact"].includes(merged.density) ? merged.density : DEFAULT_SETTINGS.density,
    stream: Boolean(merged.stream),
    confirm: Boolean(merged.confirm),
    attachMemories: Boolean(merged.attachMemories),
    autoScroll: Boolean(merged.autoScroll),
    enableThinking: Boolean(merged.enableThinking),
    openThinking: Boolean(merged.openThinking),
    detailsEnabled: Boolean(merged.detailsEnabled),
    compactTools: Boolean(merged.compactTools),
    sidebarCollapsed: Boolean(merged.sidebarCollapsed),
    journalLimit: boundedNumber(merged.journalLimit, DEFAULT_SETTINGS.journalLimit, 5, 200),
    messageWidth: boundedNumber(merged.messageWidth, DEFAULT_SETTINGS.messageWidth, 52, 120),
    memoryPrefix: boundedString(merged.memoryPrefix, DEFAULT_SETTINGS.memoryPrefix, MAX_PREFIX_CHARS).trim() || DEFAULT_SETTINGS.memoryPrefix,
    profilePrefix: boundedString(merged.profilePrefix, DEFAULT_SETTINGS.profilePrefix, MAX_PREFIX_CHARS).trim() || DEFAULT_SETTINGS.profilePrefix,
    responseFormat: boundedString(merged.responseFormat, DEFAULT_SETTINGS.responseFormat, MAX_SETTINGS_TEXT_CHARS),
    sessionSearchQuery: boundedString(merged.sessionSearchQuery, "", 1000),
    deepResearch: {
      mode: ["local", "hybrid"].includes(merged.deepResearch?.mode) ? merged.deepResearch.mode : DEFAULT_SETTINGS.deepResearch.mode,
      depth: boundedNumber(merged.deepResearch?.depth, DEFAULT_SETTINGS.deepResearch.depth, 1, 4)
    },
    runtimeTimeouts: {
      ollama: boundedNumber(merged.runtimeTimeouts?.ollama, DEFAULT_SETTINGS.runtimeTimeouts.ollama, 1, 3600),
      tools: boundedNumber(merged.runtimeTimeouts?.tools, DEFAULT_SETTINGS.runtimeTimeouts.tools, 1, 3600)
    },
    theme: normalizeTheme(merged.theme),
    modelOptions: {}
  };

  MODEL_NUMERIC_OPTION_KEYS.forEach((key) => {
    sanitized.modelOptions[key] = boundedNumber(merged.modelOptions?.[key], DEFAULT_SETTINGS.modelOptions[key]);
  });
  MODEL_BOOLEAN_OPTION_KEYS.forEach((key) => {
    sanitized.modelOptions[key] = Boolean(merged.modelOptions?.[key] ?? DEFAULT_SETTINGS.modelOptions[key]);
  });
  sanitized.modelOptions.keep_alive = boundedString(merged.modelOptions?.keep_alive, DEFAULT_SETTINGS.modelOptions.keep_alive, 200).trim();
  sanitized.modelOptions.stop = Array.isArray(merged.modelOptions?.stop)
    ? merged.modelOptions.stop.map((line) => boundedString(line, "", 500).trim()).filter(Boolean).slice(0, 32)
    : [];
  return sanitized;
}

function sanitizeProfile(rawProfile = {}) {
  const raw = rawProfile && typeof rawProfile === "object" ? rawProfile : {};
  return {
    name: boundedString(raw.name, "", 200),
    nickname: boundedString(raw.nickname, "", 200),
    about: boundedString(raw.about, "", MAX_PROFILE_TEXT_CHARS),
    preferences: boundedString(raw.preferences, "", MAX_PROFILE_TEXT_CHARS),
    other: boundedString(raw.other, "", MAX_PROFILE_TEXT_CHARS),
    userAvatar: sanitizeAvatarDataUrl(raw.userAvatar),
    assistantAvatar: sanitizeAvatarDataUrl(raw.assistantAvatar)
  };
}

function sanitizeAvatarDataUrl(value) {
  const text = String(value || "");
  if (!/^data:image\/(png|jpe?g|webp);base64,/i.test(text)) return "";
  return text.length <= MAX_AVATAR_DATA_URL_CHARS ? text : "";
}

function isQuotaExceededError(error) {
  return error?.name === "QuotaExceededError" || error?.name === "NS_ERROR_DOM_QUOTA_REACHED" || error?.code === 22 || error?.code === 1014;
}

function storageKeyLabel(key) {
  return Object.entries(STORAGE_KEYS).find(([, value]) => value === key)?.[0] || key;
}

function pruneDuplicateAndLegacyStorage() {
  LEGACY_STORAGE_KEYS.forEach((key) => {
    try { localStorage.removeItem(key); } catch {}
  });
  if (state.activeSystemPromptId || state.systemPrompts.length) {
    try { localStorage.removeItem(STORAGE_KEYS.systemPrompt); } catch {}
  }
}

function safeLocalStorageSetItem(key, value) {
  try {
    localStorage.setItem(key, value);
    return true;
  } catch (error) {
    if (!isQuotaExceededError(error)) throw error;
    pruneDuplicateAndLegacyStorage();
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (retryError) {
      if (!isQuotaExceededError(retryError)) throw retryError;
      console.warn(`Local storage quota exceeded while saving ${key}.`, retryError);
      return false;
    }
  }
}

function setRequestStats(text, { bad = false } = {}) {
  const stats = $("requestStats");
  if (!stats) return;
  stats.textContent = text;
  stats.classList.toggle("bad-text", Boolean(bad));
}

function reportStorageFailure(failedKeys) {
  if (!failedKeys.length) return;
  const names = failedKeys.map(storageKeyLabel).join(", ");
  setRequestStats(`storage full: ${names} not saved`, { bad: true });
}

function persist({ syncControls = true } = {}) {
  if (syncControls) syncSettingsFromMainControls();

  state.sessions.forEach((session) => normalizeSessionMessages(session));
  state.settings = sanitizeSettings(state.settings);
  state.profile = sanitizeProfile(state.profile);
  pruneDuplicateAndLegacyStorage();

  const legacyPrompt = !state.activeSystemPromptId && !state.systemPrompts.length
    ? boundedString($("systemPromptInput")?.value || "", "", 120000)
    : "";

  const writes = [
    [STORAGE_KEYS.schema, String(LOCAL_STORAGE_SCHEMA_VERSION)],
    [STORAGE_KEYS.activeSession, state.activeSessionId ?? ""],
    [STORAGE_KEYS.activeSystemPrompt, state.activeSystemPromptId ?? ""],
    [STORAGE_KEYS.settings, JSON.stringify(state.settings)],
    [STORAGE_KEYS.profile, JSON.stringify(state.profile)],
    [STORAGE_KEYS.memories, JSON.stringify(state.memories)],
    [STORAGE_KEYS.systemPrompts, JSON.stringify(state.systemPrompts)],
    [STORAGE_KEYS.sessions, JSON.stringify(state.sessions)]
  ];

  if (legacyPrompt) writes.push([STORAGE_KEYS.systemPrompt, legacyPrompt]);
  else {
    try { localStorage.removeItem(STORAGE_KEYS.systemPrompt); } catch {}
  }

  const failedKeys = writes
    .filter(([key, value]) => !safeLocalStorageSetItem(key, value))
    .map(([key]) => key);
  reportStorageFailure(failedKeys);
  return failedKeys.length === 0;
}

function loadLocalState() {
  const storedSchema = Number(localStorage.getItem(STORAGE_KEYS.schema) || 0);
  const oldSessions = localStorage.getItem("showcase.ui.sessions.v2");
  const oldActive = localStorage.getItem("showcase.ui.activeSession.v2");
  const oldMemories = localStorage.getItem("showcase.ui.memories.v2");
  const oldSettingsPrompt = localStorage.getItem("showcase.ui.systemPrompt.v2");
  try { state.sessions = JSON.parse(localStorage.getItem(STORAGE_KEYS.sessions) || oldSessions || "[]"); } catch { state.sessions = []; }
  try { state.memories = JSON.parse(localStorage.getItem(STORAGE_KEYS.memories) || oldMemories || "[]"); } catch { state.memories = []; }
  try { state.settings = sanitizeSettings(JSON.parse(localStorage.getItem(STORAGE_KEYS.settings) || "{}")); } catch { state.settings = structuredClone(DEFAULT_SETTINGS); }
  try { state.systemPrompts = JSON.parse(localStorage.getItem(STORAGE_KEYS.systemPrompts) || "[]"); } catch { state.systemPrompts = []; }
  try { state.profile = sanitizeProfile(JSON.parse(localStorage.getItem(STORAGE_KEYS.profile) || "{}")); } catch { state.profile = structuredClone(DEFAULT_PROFILE); }
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
  state.sessions.forEach((session) => {
    session.pinned = Boolean(session.pinned);
    session.archived = Boolean(session.archived);
    session.shared = Boolean(session.shared);
  });
  state.sessions.forEach((session) => normalizeSessionMessages(session));
  if (storedSchema !== LOCAL_STORAGE_SCHEMA_VERSION) safeLocalStorageSetItem(STORAGE_KEYS.schema, String(LOCAL_STORAGE_SCHEMA_VERSION));
  applySettingsToMainControls();
  if (!state.sessions.length) createSession(false);
  if (state.sessions.find((session) => session.id === state.activeSessionId)?.archived) state.activeSessionId = state.sessions.find((session) => !session.archived)?.id || null;
  if (!activeSession()) state.activeSessionId = state.sessions[0].id;
}

function createSession(render = true) {
  const session = { id: uid("session"), title: "New session", createdAt: new Date().toISOString(), messages: [], pinned: false, archived: false, shared: false };
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
    message: `${session.archived ? "Archived chat deletion is permanent." : "Tip: archive first if you may want this later."} This deletes “${session.title || "Untitled session"}” and its ${session.messages?.length || 0} messages from browser storage.`,
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

function togglePinSession(sessionId) {
  const session = state.sessions.find((candidate) => candidate.id === sessionId);
  if (!session) return;
  session.pinned = !session.pinned;
  persist();
  renderAll();
}

function archiveSession(sessionId) {
  const session = state.sessions.find((candidate) => candidate.id === sessionId);
  if (!session) return;
  session.archived = true;
  if (state.activeSessionId === sessionId) state.activeSessionId = state.sessions.find((candidate) => !candidate.archived && candidate.id !== sessionId)?.id || null;
  if (!activeSession()) createSession(false);
  persist();
  renderAll();
}

function restoreSession(sessionId) {
  const session = state.sessions.find((candidate) => candidate.id === sessionId);
  if (!session) return;
  session.archived = false;
  state.activeSessionId = session.id;
  persist();
  renderAll();
  setActivePage("chat");
}

async function shareSession(sessionId) {
  const session = state.sessions.find((candidate) => candidate.id === sessionId);
  if (!session) return;
  const text = JSON.stringify(session, null, 2);
  session.shared = true;
  try { await navigator.clipboard.writeText(text); }
  catch { downloadJson(`${(session.title || "session").replace(/[^a-z0-9]+/gi, "-").toLowerCase()}-share.json`, session); }
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
  renderSidebarSessions();
  renderSessionTitle();
  renderSidebarOverview();
  return message;
}

function renderAll() {
  renderSessions();
  renderMemories();
  renderChat();
  renderRuntimeStatus();
  renderHelp();
  renderSidebarSessions();
  updatePageChrome();
  applySettingsVisuals();
}

function renderSessionTitle() {
  const session = activeSession();
  const meta = PAGE_META[state.activePage] || PAGE_META.chat;

  const title =
    state.activePage === "chat"
      ? (session?.title || "New session")
      : meta.title;

  const eyebrow = meta.eyebrow;
  const summary = meta.summary;

  const pageEyebrow = $("pageEyebrow");
  const sessionTitle = $("sessionTitle");
  const pageSummary = $("pageSummary");

  if (pageEyebrow) pageEyebrow.textContent = eyebrow;
  if (sessionTitle) sessionTitle.textContent = title;
  if (pageSummary) pageSummary.textContent = summary;

  document.querySelectorAll("[data-page-eyebrow]").forEach((node) => {
    node.textContent = eyebrow;
  });

  document.querySelectorAll("[data-page-title]").forEach((node) => {
    node.textContent = title;
  });

  document.querySelectorAll("[data-page-summary]").forEach((node) => {
    node.textContent = summary;
  });
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
  if (state.settings.mode === "user" && ["tools", "journal"].includes(state.activePage)) state.activePage = "chat";
  updatePageChrome();
  if (state.activePage === "journal") loadJournal();
  if (closeDrawer) closeMobileDrawers();
}

function renderSidebarOverview() {
  const session = activeSession();
  const activeSessions = state.sessions.filter((item) => !item.archived);
  const archivedSessions = state.sessions.filter((item) => item.archived);
  const messages = state.sessions.reduce((sum, item) => sum + (item.messages?.length || 0), 0);
  const toolCalls = state.sessions.reduce((sum, item) => sum + (item.messages || []).reduce((inner, msg) => inner + (msg.toolCalls || []).length, 0), 0);
  const overview = $("overviewGrid");
  if (overview) {
    overview.innerHTML = `
    <div class="overview-tile large"><strong>${activeSessions.length}</strong><span>active chats</span></div>
    <div class="overview-tile large"><strong>${archivedSessions.length}</strong><span>archived chats</span></div>
    <div class="overview-tile"><strong>${messages}</strong><span>total messages</span></div>
    <div class="overview-tile"><strong>${state.models.length || "-"}</strong><span>local models</span></div>
    <div class="overview-tile dev-only"><strong>${state.tools.length || "-"}</strong><span>runtime tools</span></div>
    <div class="overview-tile dev-only"><strong>${state.journal.length || "-"}</strong><span>events loaded</span></div>
    <div class="overview-tile"><strong>${state.memories.length}</strong><span>memories</span></div>
    <div class="overview-tile dev-only"><strong>${toolCalls}</strong><span>tool calls</span></div>
    <div class="overview-tile"><strong>${state.settings.mode}</strong><span>interface mode</span></div>
    <div class="overview-tile"><strong>${state.settings.stream ? "on" : "off"}</strong><span>streaming</span></div>`;
  }
  renderSidebarSessions();
  applyModeVisibility();
}

function plannerSafeToolCount() {
  return state.tools.map((tool) => toolId(tool)).filter((id) => PLANNER_SAFE_TOOLS.has(id)).length;
}

function runtimeReadiness() {
  const selectedModel = $("modelSelect")?.value || "auto route";
  const toolTotal = state.tools.length || state.runtime?.tools?.length || 0;
  const journalKnown = Boolean(state.journalStats.path || state.runtime?.journal?.path || state.journal.length);
  return [
    { label: "Ollama", value: state.modelsOk === null ? "checking" : state.modelsOk ? "online" : "offline", status: state.modelsOk ? "ok" : state.modelsOk === false ? "bad" : "muted", detail: state.modelsOk ? `${state.models.length} local models` : "start Ollama or check endpoint" },
    { label: "Model", value: selectedModel, status: selectedModel === "auto route" ? "muted" : "ok", detail: selectedModel === "auto route" ? "server routing enabled" : "manual override" },
    { label: "Tools", value: `${plannerSafeToolCount()}/${toolTotal || "-"}`, status: toolTotal ? "ok" : "bad", detail: "planner-safe / runtime" },
    { label: "Mode", value: state.settings.mode || "dev", status: "muted", detail: state.settings.mode === "user" ? "clean interface" : "developer surfaces" },
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
  const activeSessions = state.sessions.filter((session) => !session.archived);
  const sessions = (query
    ? activeSessions.filter((session) => JSON.stringify(session).toLowerCase().includes(query))
    : activeSessions)
    .sort((a, b) => Number(Boolean(b.pinned)) - Number(Boolean(a.pinned)) || new Date(b.messages?.at(-1)?.createdAt || b.createdAt) - new Date(a.messages?.at(-1)?.createdAt || a.createdAt));
  if (!sessions.length) {
    root.innerHTML = `<div class="session-item diagnostic-card"><strong>No matching chats</strong><span>Search did not match local session titles or messages.</span></div>`;
    renderSidebarSessions();
    return;
  }
  sessions.forEach((session) => {
    const item = document.createElement("div");
    item.className = `session-item clickable-card ${session.id === state.activeSessionId ? "active" : ""} ${session.pinned ? "pinned" : ""}`;
    const count = session.messages.length;
    const updated = session.messages.at(-1)?.createdAt || session.createdAt;
    item.innerHTML = `
      <button class="session-main" data-action="open" title="Open session">
        <strong>${session.pinned ? "★ " : ""}${escapeHtml(session.title)}</strong>
        <span>${count} messages · ${new Date(updated).toLocaleString()}</span>
      </button>
      <details class="session-menu"><summary aria-label="Chat menu">⋯</summary><div class="session-menu-popover">
        <button class="ghost-button" data-action="pin">${session.pinned ? "Unpin" : "Pin"}</button>
        <button class="ghost-button" data-action="rename">Rename</button>
        <button class="ghost-button" data-action="share">Share</button>
        <button class="ghost-button" data-action="archive">Archive</button>
        <button class="danger-button" data-action="delete">Delete</button>
      </div></details>`;
    item.querySelector("[data-action=\"open\"]").addEventListener("click", (event) => {
      if (event.altKey) return openSessionDetail(session);
      state.activeSessionId = session.id;
      persist();
      renderAll();
      setActivePage("chat");
    });
    item.querySelector("[data-action=\"pin\"]").addEventListener("click", (event) => { event.stopPropagation(); togglePinSession(session.id); });
    item.querySelector("[data-action=\"rename\"]").addEventListener("click", (event) => { event.stopPropagation(); renameSession(session.id); });
    item.querySelector("[data-action=\"share\"]").addEventListener("click", (event) => { event.stopPropagation(); shareSession(session.id); });
    item.querySelector("[data-action=\"archive\"]").addEventListener("click", (event) => { event.stopPropagation(); archiveSession(session.id); });
    item.querySelector("[data-action=\"delete\"]").addEventListener("click", (event) => { event.stopPropagation(); requestDeleteSession(session.id); });
    item.addEventListener("dblclick", () => openSessionDetail(session));
    root.appendChild(item);
  });
  renderArchiveList();
  renderSidebarSessions();
}

function renderArchiveList() {
  const root = $("archiveList");
  const count = $("archiveCount");
  if (!root) return;
  const archived = state.sessions.filter((session) => session.archived).sort((a, b) => new Date(b.messages?.at(-1)?.createdAt || b.createdAt) - new Date(a.messages?.at(-1)?.createdAt || a.createdAt));
  if (count) count.textContent = String(archived.length);
  if (!archived.length) {
    root.innerHTML = `<div class="session-item diagnostic-card"><span>No archived chats.</span></div>`;
    return;
  }
  root.innerHTML = "";
  archived.forEach((session) => {
    const item = document.createElement("div");
    item.className = "session-item archived clickable-card";
    item.innerHTML = `<strong>${escapeHtml(session.title || "Archived chat")}</strong><span>${session.messages?.length || 0} messages</span><div class="session-actions"><button class="ghost-button" data-action="restore">Restore</button><button class="danger-button" data-action="delete">Delete forever</button></div>`;
    item.querySelector('[data-action="restore"]').addEventListener("click", (event) => { event.stopPropagation(); restoreSession(session.id); });
    item.querySelector('[data-action="delete"]').addEventListener("click", (event) => { event.stopPropagation(); requestDeleteSession(session.id); });
    item.addEventListener("dblclick", () => openSessionDetail(session));
    root.appendChild(item);
  });
}

function sidebarSessions() {
  const query = state.sessionSearchQuery.trim().toLowerCase();

  return state.sessions
    .filter((session) => !session.archived)
    .filter((session) => {
      if (!query) return true;
      return JSON.stringify(session).toLowerCase().includes(query);
    })
    .sort((a, b) =>
      Number(Boolean(b.pinned)) - Number(Boolean(a.pinned)) ||
      new Date(b.messages?.at(-1)?.createdAt || b.createdAt) -
      new Date(a.messages?.at(-1)?.createdAt || a.createdAt)
    );
}

function renderSidebarSessions() {
  const root = $("sidebarSessionHistory");
  const count = $("sidebarChatCount");
  if (!root) return;

  const sessions = sidebarSessions();
  if (count) count.textContent = String(sessions.length);

  if (!sessions.length) {
    root.innerHTML = `
      <div class="sidebar-empty-chat">
        <strong>No chats found</strong>
        <span>Start a new chat or clear the search.</span>
      </div>`;
    return;
  }

  const pinned = sessions.filter((session) => session.pinned);
  const recent = sessions.filter((session) => !session.pinned);

  root.innerHTML = `
    ${pinned.length ? sidebarSessionGroupHtml("Pinned", pinned) : ""}
    ${sidebarSessionGroupHtml("Recent", recent)}
  `;

  wireSidebarSessionRows(root);
}

function sidebarSessionGroupHtml(label, sessions) {
  if (!sessions.length) return "";
  return `
    <div class="sidebar-chat-group">
      <div class="sidebar-chat-group-title">${escapeHtml(label)}</div>
      ${sessions.map(sidebarSessionRowHtml).join("")}
    </div>
  `;
}

function sidebarSessionRowHtml(session) {
  const lastMessage = [...(session.messages || [])]
    .reverse()
    .find((message) => String(message.content || "").trim());

  const snippet = String(lastMessage?.content || "New conversation")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 78);

  return `
    <div class="sidebar-chat-row ${session.id === state.activeSessionId ? "active" : ""}" data-session-row="${escapeHtml(session.id)}">
      <button class="sidebar-chat-open" data-open-session="${escapeHtml(session.id)}">
        <strong>${escapeHtml(session.title || "New session")}</strong>
        <span>${escapeHtml(snippet)}</span>
      </button>
      <button class="sidebar-chat-menu-button" data-open-session-menu="${escapeHtml(session.id)}" aria-label="Chat options">⋯</button>
    </div>
  `;
}

function openSidebarSessionFromRail(sessionId) {
  const session = state.sessions.find((candidate) => candidate.id === sessionId && !candidate.archived);
  if (!session) return;

  state.activeSessionId = session.id;
  state.activePage = "chat";
  closeSidebarSessionMenu();
  persist();
  renderAll();
  closeMobileDrawers();

  requestAnimationFrame(() => {
    const prompt = $("promptInput");
    if (prompt && !window.matchMedia("(max-width: 760px)").matches) {
      prompt.focus({ preventScroll: true });
    }
  });
}

function wireSidebarSessionRows(root) {
  root.querySelectorAll("[data-session-row]").forEach((row) => {
    row.tabIndex = 0;
    row.setAttribute("role", "button");

    row.addEventListener("click", (event) => {
      if (event.target.closest("[data-open-session-menu]")) return;
      event.preventDefault();
      event.stopPropagation();
      openSidebarSessionFromRail(row.dataset.sessionRow);
    });

    row.addEventListener("keydown", (event) => {
      if (!["Enter", " "].includes(event.key)) return;
      event.preventDefault();
      openSidebarSessionFromRail(row.dataset.sessionRow);
    });
  });

  root.querySelectorAll("[data-open-session]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openSidebarSessionFromRail(button.dataset.openSession);
    });
  });

  root.querySelectorAll("[data-open-session-menu]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openSidebarSessionMenu(button.dataset.openSessionMenu, button);
    });
  });
}

let activeSidebarMenuSessionId = null;

function openSidebarSessionMenu(sessionId, anchor) {
  const menu = $("sidebarSessionMenu");
  const session = state.sessions.find((candidate) => candidate.id === sessionId);
  if (!menu || !session || !anchor) return;

  activeSidebarMenuSessionId = sessionId;

  menu.querySelector('[data-session-menu="pin"]').textContent = session.pinned ? "Unpin" : "Pin";

  const rect = anchor.getBoundingClientRect();
  const menuWidth = 170;
  const menuHeight = 210;

  const left = Math.min(
    window.innerWidth - menuWidth - 10,
    Math.max(10, rect.right - menuWidth)
  );

  const top = Math.min(
    window.innerHeight - menuHeight - 10,
    Math.max(10, rect.bottom + 6)
  );

  menu.style.left = `${left}px`;
  menu.style.top = `${top}px`;
  menu.hidden = false;
}

function closeSidebarSessionMenu() {
  const menu = $("sidebarSessionMenu");
  if (menu) menu.hidden = true;
  activeSidebarMenuSessionId = null;
}

function wireSidebarSessionMenu() {
  const menu = $("sidebarSessionMenu");
  if (!menu) return;

  menu.querySelectorAll("[data-session-menu]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();

      const sessionId = activeSidebarMenuSessionId;
      if (!sessionId) return;

      const action = button.dataset.sessionMenu;
      closeSidebarSessionMenu();

      if (action === "pin") togglePinSession(sessionId);
      if (action === "rename") renameSession(sessionId);
      if (action === "share") shareSession(sessionId);
      if (action === "archive") archiveSession(sessionId);
      if (action === "delete") requestDeleteSession(sessionId);
    });
  });

  document.addEventListener("click", (event) => {
    if (!menu.hidden && !menu.contains(event.target)) {
      closeSidebarSessionMenu();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeSidebarSessionMenu();
    }
  });

  window.addEventListener("resize", closeSidebarSessionMenu);
  window.addEventListener("scroll", closeSidebarSessionMenu, true);
}

function wireSidebarSearch() {
  const button = $("sidebarSearchBtn");
  const shell = $("sidebarSearchShell");
  const input = $("sidebarSearchInput");

  if (!button || !shell || !input) return;

  button.addEventListener("click", () => {
    shell.hidden = !shell.hidden;
    button.setAttribute("aria-expanded", String(!shell.hidden));
    if (!shell.hidden) input.focus({ preventScroll: true });
  });

  input.addEventListener("input", () => {
    state.sessionSearchQuery = input.value;
    renderSessions();
  });
}

function toggleRecentSessionsPullout() {
  const root = $("recentSessionsPullout");
  if (!root) return;
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

  const wasHidden = box.hidden;
  box.hidden = false;
  if (wasHidden) box.open = Boolean(state.settings.openThinking);
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
  const openToolKeys = new Set(
    Array.from(root.querySelectorAll(".tool-call[open]"))
      .map((node) => node.dataset.toolKey)
      .filter(Boolean)
  );
  root.innerHTML = "";
  calls.forEach((call, index) => {
    const card = document.createElement(nested ? "details" : "section");
    card.className = `tool-call clickable-card${nested ? " nested-tool-call" : ""}`;
    const toolKey = toolCallRenderKey(call, index);
    card.dataset.toolKey = toolKey;
    if (nested && openToolKeys.has(toolKey)) card.open = true;
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

function toolCallRenderKey(call, index) {
  const name = call.tool_name || call.name || "tool";
  const args = JSON.stringify(call.data?.arguments || call.arguments || {});
  return `${index}:${name}:${args}`;
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
  if (!root) {
    updateModelMeta();
    return;
  }
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
  const metaText = $("modelMetaText");
  const label = !value ? "Auto route" : `${profile?.category || live?.details?.family || "local"}${live?.size ? ` · ${prettyBytes(live.size)}` : ""}`;
  if (metaText) metaText.textContent = !value ? "Auto route selects a model per request." : label;
  if (!root) return;
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

function renderModelOptionControls() {
  const stepFor = (key) => ["temperature", "top_p", "min_p", "typical_p", "repeat_penalty", "presence_penalty", "frequency_penalty"].includes(key) ? "0.01" : "1";
  Object.entries(MODEL_OPTION_GROUPS).forEach(([rootId, keys]) => {
    const root = $(rootId);
    if (!root) return;
    root.innerHTML = keys.map((key) => {
      const label = MODEL_OPTION_LABELS[key] || key.replaceAll("_", " ");
      if (MODEL_BOOLEAN_OPTION_KEYS.includes(key)) {
        return `<label class="setting-line compact-setting-line"><span>${escapeHtml(label)}</span><input id="settingsModel_${escapeHtml(key)}" type="checkbox" /></label>`;
      }
      return `<label class="number-field"><span>${escapeHtml(label)}</span><input id="settingsModel_${escapeHtml(key)}" type="number" step="${stepFor(key)}" /></label>`;
    }).join("");
  });
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
  MODEL_NUMERIC_OPTION_KEYS.forEach((key) => {
    const value = Number(opts[key]);
    if (!Number.isFinite(value)) return;
    if (["seed", "num_predict", "num_keep", "num_gpu"].includes(key) && value < 0) return;
    if (["num_thread"].includes(key) && value <= 0) return;
    out[key] = value;
  });
  MODEL_BOOLEAN_OPTION_KEYS.forEach((key) => {
    if (typeof opts[key] === "boolean") out[key] = opts[key];
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

function selectedDeepResearchOptions() {
  return {
    mode: ["local", "hybrid"].includes($("composerResearchModeSelect")?.value) ? $("composerResearchModeSelect").value : state.settings.deepResearch.mode,
    depth: Math.max(1, Math.min(4, Number($("composerResearchDepthSelect")?.value || state.settings.deepResearch.depth || 2)))
  };
}

function chatContextRole(role) {
  if (role === "user") return "user";
  if (role === "assistant") return "assistant";
  return null;
}

function messageTextForContext(message) {
  ensureMessageVariants(message);
  return String(message?.content || "").trim();
}

function trimChatContextMessages(messages, maxMessages = CHAT_CONTEXT_MAX_MESSAGES, maxChars = CHAT_CONTEXT_MAX_CHARS) {
  const trimmed = messages.slice(-Math.max(1, maxMessages));
  let total = trimmed.reduce((sum, message) => sum + message.content.length, 0);
  while (trimmed.length > 1 && total > maxChars) {
    const removed = trimmed.shift();
    total -= removed?.content?.length || 0;
  }
  return trimmed;
}

function buildChatContextMessages({ assistantMessage = null, requestText = "", userText = "" } = {}) {
  const session = activeSession();
  if (!session?.messages?.length) {
    const fallback = String(requestText || userText || "").trim();
    return fallback ? [{ role: "user", content: fallback }] : [];
  }

  const assistantIndex = assistantMessage?.id
    ? session.messages.findIndex((message) => message.id === assistantMessage.id)
    : -1;
  const stopIndex = assistantIndex >= 0 ? assistantIndex : session.messages.length;
  const parentUserId = assistantMessage?.parentUserMessageId || null;
  const effectiveRequestText = String(requestText || userText || "").trim();
  const messages = [];

  session.messages.slice(0, stopIndex).forEach((message) => {
    const role = chatContextRole(message.role);
    if (!role) return;
    let content = messageTextForContext(message);
    if (role === "user" && parentUserId && message.id === parentUserId && effectiveRequestText) {
      content = effectiveRequestText;
    }
    if (!content) return;
    const previous = messages[messages.length - 1];
    if (previous?.role === role) previous.content = `${previous.content}\n\n${content}`;
    else messages.push({ role, content });
  });

  if (effectiveRequestText && messages[messages.length - 1]?.content !== effectiveRequestText) {
    messages.push({ role: "user", content: effectiveRequestText });
  }

  return trimChatContextMessages(messages);
}

function previewAutoRoute(text) {
  if ($("modelSelect").value) return;
  const profile = routeModelForText(text);
  if (!profile) return;
  setRequestStats(`auto → ${profile.category}`);
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
  if (state.composerDeepResearch) {
    await requestDeepResearchResponse({ userText: text, assistantMessage, assistantNode });
    return;
  }
  await requestAssistantResponse({ userText: text, requestText: text, assistantMessage, assistantNode });
}

async function requestDeepResearchResponse({ userText, assistantMessage, assistantNode }) {
  if (state.busy) return;
  state.busy = true;
  const started = performance.now();
  const contentNode = assistantNode?.querySelector(".message-content");
  const options = selectedDeepResearchOptions();
  patchActiveMessageVariant(assistantMessage, {
    content: "Starting local deep research...",
    thinking: `Mode: ${options.mode}\nDepth: ${options.depth}`,
    toolCalls: [],
    ok: true,
    model: "local research",
    requestText: userText
  });
  renderMessageContent(contentNode, assistantMessage);
  renderActivityBox(assistantNode, assistantMessage);
  setRequestStats(`deep research · depth ${options.depth}`);
  $("sendBtn").textContent = "X";
  $("sendBtn").title = "Deep research running";
  try {
    const start = await researchApi("/api/research/start", { goal: userText, mode: options.mode, depth: options.depth });
    patchActiveMessageVariant(assistantMessage, {
      content: "Research plan created. Gathering local sources...",
      toolCalls: [{ tool_name: "research.start", ok: true, summary: `${start.session?.plan?.length || 0} plan steps`, data: start.session || {} }]
    });
    renderMessageContent(contentNode, assistantMessage);
    renderActivityBox(assistantNode, assistantMessage);
    const run = await researchApi("/api/research/run", { id: start.session.id });
    const session = run.session || {};
    patchActiveMessageVariant(assistantMessage, {
      content: session.report || "Deep research completed without a report.",
      thinking: (session.plan || []).map((item, index) => `${index + 1}. ${item}`).join("\n"),
      toolCalls: [
        { tool_name: "research.start", ok: true, summary: `${start.session?.plan?.length || 0} plan steps`, data: start.session || {} },
        { tool_name: "research.run", ok: true, summary: `${(session.sources || []).length} sources`, data: session }
      ],
      ok: true,
      modelRoute: { category: "deep research", reason: "composer deep research" }
    });
    assistantNode.classList.toggle("failed", false);
    renderMessageContent(contentNode, assistantMessage);
    renderActivityBox(assistantNode, assistantMessage);
    renderMessageActions(assistantNode, assistantMessage);
  } catch (error) {
    patchActiveMessageVariant(assistantMessage, { ok: false, content: `Deep research failed: ${error.message}` });
    assistantNode.classList.toggle("failed", true);
    renderMessageContent(contentNode, assistantMessage);
    renderMessageActions(assistantNode, assistantMessage);
  } finally {
    patchActiveMessageVariant(assistantMessage, { latencyMs: Math.round(performance.now() - started) });
    persist();
    state.busy = false;
    $("sendBtn").textContent = ">";
    $("sendBtn").title = "Send";
    setRequestStats(`${assistantMessage.latencyMs} ms · deep research`);
    await loadJournal();
    scrollChat();
  }
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
    messages: buildChatContextMessages({ assistantMessage, requestText: requestText || userText, userText }),
    ...buildRuntimeTimeouts()
  };
  setRequestStats("running...");
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
    setRequestStats(`${assistantMessage.latencyMs} ms · ${assistantMessage.content.length} chars`);
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
  if (state.busy) return;
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
  if (state.busy) return;
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
  return {
    tool_call: {
      tool_name: tool,
      ok: false,
      summary: "/api/tool failed or is unavailable. Refusing to fallback to /api/ask because that would start a hidden model request.",
      data: { fallback: false, arguments: args }
    }
  };
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

  if ($("streamToggle")) $("streamToggle").checked = Boolean(state.settings.stream);
  if ($("confirmToggle")) $("confirmToggle").checked = Boolean(state.settings.confirm);
  if ($("memoryToggle")) $("memoryToggle").checked = Boolean(state.settings.attachMemories);
  if ($("autoScrollToggle")) $("autoScrollToggle").checked = Boolean(state.settings.autoScroll);
  if ($("composerResearchDepthSelect")) $("composerResearchDepthSelect").value = String(state.settings.deepResearch?.depth || DEFAULT_SETTINGS.deepResearch.depth);
  if ($("composerResearchModeSelect")) $("composerResearchModeSelect").value = state.settings.deepResearch?.mode || DEFAULT_SETTINGS.deepResearch.mode;

  applySettingsVisuals();
}

function applySettingsVisuals() {
  document.documentElement.dataset.density = state.settings.density || "comfortable";
  document.documentElement.dataset.compactTools = state.settings.compactTools ? "true" : "false";
  document.documentElement.style.setProperty("--message-max", `${Number(state.settings.messageWidth) || 78}ch`);
  document.body.classList.toggle("sidebar-collapsed", Boolean(state.settings.sidebarCollapsed));

  const theme = normalizeTheme(state.settings.theme);
  setThemeHexVar("--bg", theme, "primary");
  setThemeHexVar("--bg-2", theme, "backgroundSoft");
  setThemeHexVar("--bg-start", theme, "backgroundStart");
  setThemeHexVar("--bg-end", theme, "backgroundEnd");
  setThemeRgbaVar("--bg-glow", theme, "backgroundGlow", 0.16);
  setThemeRgbaVar("--bg-glow-2", theme, "backgroundGlowTwo", 0.14);
  setThemeHexVar("--text", theme, "text");
  setThemeHexVar("--muted", theme, "muted");
  setThemeHexVar("--muted-2", theme, "mutedTwo");
  setThemeHexVar("--accent", theme, "accent");
  setThemeHexVar("--accent-2", theme, "accentTwo");
  setThemeHexVar("--accent-contrast", theme, "accentContrast");
  setThemeHexVar("--warn", theme, "warn");
  setThemeHexVar("--bad", theme, "bad");
  setThemeHexVar("--bad-text", theme, "badText");
  setThemeHexVar("--ok", theme, "ok");
  setThemeHexVar("--code-text", theme, "codeText");
  setThemeHexVar("--thinking-text", theme, "thinkingText");

  setThemeRgbaVar("--panel", theme, "panel", 0.74);
  setThemeRgbaVar("--panel-strong", theme, "panelStrong", 0.92);
  setThemeRgbaVar("--glass-start", theme, "panel", 0.78);
  setThemeRgbaVar("--glass-end", theme, "input", 0.76);
  setThemeRgbaVar("--drawer-start", theme, "panel", 0.96);
  setThemeRgbaVar("--drawer-end", theme, "input", 0.98);
  setThemeRgbaVar("--popover-bg", theme, "input", 0.96);
  setThemeRgbaVar("--menu-bg", theme, "input", 0.98);
  setThemeRgbaVar("--input-bg", theme, "input", 0.46);
  setThemeRgbaVar("--input-bg-soft", theme, "input", 0.26);
  setThemeRgbaVar("--input-bg-medium", theme, "input", 0.35);
  setThemeRgbaVar("--input-bg-focus", theme, "input", 0.62);

  setThemeRgbaVar("--line", theme, "line", 0.13);
  setThemeRgbaVar("--line-strong", theme, "lineStrong", 0.25);
  setThemeRgbaVar("--line-soft", theme, "line", 0.08);
  setThemeRgbaVar("--line-soft-2", theme, "line", 0.11);

  [0.025, 0.03, 0.035, 0.04, 0.055].forEach((alpha) => {
    setThemeRgbaVar(`--surface-${String(alpha).replace("0.", "")}`, theme, "surface", alpha);
  });
  [0.16, 0.18, 0.2, 0.22, 0.24, 0.28, 0.32, 0.54].forEach((alpha) => {
    setThemeRgbaVar(`--surface-dark-${String(alpha).replace("0.", "")}`, theme, "surfaceDark", alpha);
  });
  [0.055, 0.06, 0.07, 0.075, 0.08, 0.09, 0.12, 0.16, 0.18, 0.22, 0.28, 0.32, 0.34, 0.35, 0.36, 0.5, 0.55, 0.58, 0.9].forEach((alpha) => {
    setThemeRgbaVar(`--accent-${String(alpha).replace("0.", "").replace(".", "")}`, theme, "accent", alpha);
  });
  [0.16, 0.35, 0.8, 0.9].forEach((alpha) => {
    setThemeRgbaVar(`--accent-two-${String(alpha).replace("0.", "").replace(".", "")}`, theme, "accentTwo", alpha);
  });
  [0.68, 0.72, 0.78, 0.82].forEach((alpha) => {
    setThemeRgbaVar(`--accent-contrast-${String(alpha).replace("0.", "")}`, theme, "accentContrast", alpha);
  });
  [0.045, 0.05, 0.16, 0.22, 0.26, 0.28, 0.36].forEach((alpha) => {
    setThemeRgbaVar(`--warn-${String(alpha).replace("0.", "").replace(".", "")}`, theme, "warn", alpha);
  });
  [0.055, 0.06, 0.28, 0.34, 0.42].forEach((alpha) => {
    setThemeRgbaVar(`--bad-${String(alpha).replace("0.", "").replace(".", "")}`, theme, "bad", alpha);
  });
  [0.055, 0.26, 0.28].forEach((alpha) => {
    setThemeRgbaVar(`--ok-${String(alpha).replace("0.", "").replace(".", "")}`, theme, "ok", alpha);
  });

  setThemeRgbaVar("--shadow-color", theme, "shadow", 0.38);
  setThemeRgbaVar("--shadow-soft", theme, "shadow", 0.32);
  setThemeRgbaVar("--shadow-popup", theme, "shadow", 0.28);
  document.documentElement.style.setProperty("--shadow", `0 24px 70px ${hexToRgba(theme.shadow, 0.38, themeFieldDefault("shadow"))}`);
  document.documentElement.style.setProperty("--brand-shadow", `0 14px 40px ${hexToRgba(theme.accent, 0.18, themeFieldDefault("accent"))}`);
  setThemeRgbaVar("--grid-line", theme, "grid", 0.018);
  setThemeRgbaVar("--scrim", theme, "overlay", 0.54);
  setThemeRgbaVar("--mask", theme, "overlay", 0.75);
  setThemeRgbaVar("--user-avatar-strong", theme, "userAvatar", 0.9);
  setThemeRgbaVar("--user-avatar-soft", theme, "userAvatar", 0.16);

  const metaTheme = document.querySelector('meta[name="theme-color"]');
  if (metaTheme) metaTheme.setAttribute("content", normalizeHex(theme.primary, themeFieldDefault("primary")));

  document.documentElement.style.setProperty("--font", fontStack(theme.font));
  applyModeVisibility();
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

function saveSystemPromptFromEditor({ persistNow = true } = {}) {
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
  if (persistNow) persist();
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

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => resolve(String(reader.result || "")));
    reader.addEventListener("error", () => reject(reader.error || new Error("Image read failed")));
    reader.readAsDataURL(file);
  });
}

function imageFromDataUrl(dataUrl) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.addEventListener("load", () => resolve(image));
    image.addEventListener("error", () => reject(new Error("Image decode failed")));
    image.src = dataUrl;
  });
}

async function compactAvatarFile(file) {
  const originalDataUrl = await readFileAsDataUrl(file);
  if (originalDataUrl.length <= MAX_AVATAR_DATA_URL_CHARS) return originalDataUrl;

  const image = await imageFromDataUrl(originalDataUrl);
  const scale = Math.min(1, MAX_AVATAR_DIMENSION / Math.max(image.naturalWidth || image.width, image.naturalHeight || image.height));
  const width = Math.max(1, Math.round((image.naturalWidth || image.width) * scale));
  const height = Math.max(1, Math.round((image.naturalHeight || image.height) * scale));
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  context.drawImage(image, 0, 0, width, height);

  const preferredType = file.type === "image/png" ? "image/png" : "image/webp";
  let compact = canvas.toDataURL(preferredType, 0.82);
  if (compact.length > MAX_AVATAR_DATA_URL_CHARS) compact = canvas.toDataURL("image/jpeg", 0.76);
  if (compact.length > MAX_AVATAR_DATA_URL_CHARS) compact = canvas.toDataURL("image/jpeg", 0.62);
  return compact.length <= MAX_AVATAR_DATA_URL_CHARS ? compact : "";
}

async function handleAvatarUpload(kind, file) {
  if (!file) return;
  if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
    openCollectionDetail("Unsupported image", "Use a PNG, JPG, or WebP image for profile icons.", { type: file.type, name: file.name });
    return;
  }
  try {
    const dataUrl = await compactAvatarFile(file);
    if (!dataUrl) {
      openCollectionDetail("Image too large", "That avatar is still too large for browser-local storage after compression. Try a smaller square image.", { type: file.type, name: file.name, size: file.size });
      return;
    }
    if (kind === "user") state.profile.userAvatar = dataUrl;
    else state.profile.assistantAvatar = dataUrl;
    updateAvatarPreviews();
    persist();
    renderChat();
  } catch (error) {
    openCollectionDetail("Avatar upload failed", error.message || "The browser could not read that image.", { type: file.type, name: file.name, size: file.size });
  }
}

function syncSettingsModal() {
  populateSettingsModelSelect();
  renderModelOptionControls();
  renderThemePresetSelect();
  $("settingsModelSelect").value = $("modelSelect").value || "";
  $("settingsModeSelect").value = state.settings.mode || "dev";
  $("settingsDensitySelect").value = state.settings.density || "comfortable";
  $("settingsStreamToggle").checked = Boolean(state.settings.stream);
  $("settingsConfirmToggle").checked = Boolean(state.settings.confirm);
  $("settingsMemoryToggle").checked = Boolean(state.settings.attachMemories);
  $("settingsAutoScrollToggle").checked = Boolean(state.settings.autoScroll);
  $("settingsResearchDepthSelect").value = String(state.settings.deepResearch?.depth || DEFAULT_SETTINGS.deepResearch.depth);
  $("settingsResearchModeSelect").value = state.settings.deepResearch?.mode || DEFAULT_SETTINGS.deepResearch.mode;
  $("settingsOpenThinkingToggle").checked = Boolean(state.settings.openThinking);
  $("settingsDetailsToggle").checked = Boolean(state.settings.detailsEnabled);
  $("settingsCompactToolsToggle").checked = Boolean(state.settings.compactTools);
  $("settingsJournalLimit").value = state.settings.journalLimit || 50;
  $("settingsMessageWidth").value = state.settings.messageWidth || 78;
  const theme = normalizeTheme(state.settings.theme);
  THEME_COLOR_FIELDS.forEach(({ key }) => {
    const input = $(`theme${toPascalCase(key)}Color`);
    if (input) input.value = theme[key];
  });
  $("themeFontSelect").value = theme.font || "system";
  $("settingsMemoryPrefix").value = state.settings.memoryPrefix || DEFAULT_SETTINGS.memoryPrefix;
  $("settingsResponseFormat").value = state.settings.responseFormat || "";
  const opts = state.settings.modelOptions || {};
  const runtimeTimeouts = state.settings.runtimeTimeouts || DEFAULT_SETTINGS.runtimeTimeouts;
  $("settingsOllamaTimeout").value = runtimeTimeouts.ollama ?? DEFAULT_SETTINGS.runtimeTimeouts.ollama;
  $("settingsToolTimeout").value = runtimeTimeouts.tools ?? DEFAULT_SETTINGS.runtimeTimeouts.tools;
  MODEL_NUMERIC_OPTION_KEYS.forEach((key) => {
    const input = $(`settingsModel_${key}`);
    if (input) input.value = opts[key] ?? DEFAULT_SETTINGS.modelOptions[key] ?? "";
  });
  MODEL_BOOLEAN_OPTION_KEYS.forEach((key) => {
    const input = $(`settingsModel_${key}`);
    if (input) input.checked = Boolean(opts[key] ?? DEFAULT_SETTINGS.modelOptions[key]);
  });
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

function renderThemePresetSelect() {
  const select = $("themePresetSelect");
  if (!select) return;
  select.innerHTML = '<option value="">Custom</option>' + Object.entries(THEME_PRESETS).map(([id, preset]) => `<option value="${escapeHtml(id)}">${escapeHtml(preset.label)}</option>`).join("");
}

function toPascalCase(value) {
  return String(value || "").replace(/(^|[^a-z0-9])([a-z0-9])/gi, (_, __, letter) => letter.toUpperCase());
}

function themeInputId(key) {
  return `theme${toPascalCase(key)}Color`;
}

function readThemeFromControls(fallbackTheme = state.settings.theme) {
  const fallback = normalizeTheme(fallbackTheme);
  const next = {};
  THEME_COLOR_FIELDS.forEach(({ key }) => {
    next[key] = settingValue(themeInputId(key), fallback[key]);
  });
  next.font = settingValue("themeFontSelect", fallback.font || DEFAULT_THEME.font);
  return normalizeTheme(next);
}

function applyThemePreset(id) {
  const preset = THEME_PRESETS[id];
  if (!preset) return;
  const { label: _label, ...colors } = preset;
  state.settings.theme = normalizeTheme(colors);
  THEME_COLOR_FIELDS.forEach(({ key }) => {
    const input = $(themeInputId(key));
    if (input) input.value = state.settings.theme[key];
  });
  if ($("themeFontSelect")) $("themeFontSelect").value = state.settings.theme.font;
  applySettingsVisuals();
}

function renderHelp() {
  const nav = $("helpTopicNav");
  const body = $("helpTopicBody");
  if (!nav || !body) return;

  const previousActive = nav.querySelector(".active")?.dataset.helpTopic;
  const active = HELP_TOPICS.some((topic) => topic.id === previousActive)
    ? previousActive
    : HELP_TOPICS[0].id;

  nav.innerHTML = HELP_TOPICS.map((topic) => `
    <button class="help-topic-button ${topic.id === active ? "active" : ""}" data-help-topic="${escapeHtml(topic.id)}">
      <strong>${escapeHtml(topic.title)}</strong>
      <span>${escapeHtml(topic.summary || "")}</span>
    </button>
  `).join("");

  const topic = HELP_TOPICS.find((item) => item.id === active) || HELP_TOPICS[0];

  const asArray = (value) => Array.isArray(value) ? value : [value].filter(Boolean);

  const renderParagraphs = (items) => asArray(items)
    .map((item) => `<p>${escapeHtml(item)}</p>`)
    .join("");

  const renderList = (items, className) => Array.isArray(items) && items.length
    ? `<ul class="${className}">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
    : "";

  const sections = Array.isArray(topic.sections) && topic.sections.length
    ? topic.sections
    : [{ title: "Overview", body: topic.body || "" }];

  body.innerHTML = `
    <div class="help-topic-title-row">
      <div>
        <p class="eyebrow">Help guide</p>
        <h2>${escapeHtml(topic.title)}</h2>
      </div>
      ${topic.summary ? `<p class="help-topic-meta">${escapeHtml(topic.summary)}</p>` : ""}
    </div>

    ${sections.map((section) => `
      <section class="help-topic-card">
        <h3>${escapeHtml(section.title)}</h3>
        ${renderParagraphs(section.body)}
      </section>
    `).join("")}

    ${Array.isArray(topic.checklist) && topic.checklist.length ? `
      <section class="help-topic-card help-callout">
        <h3>Checklist</h3>
        ${renderList(topic.checklist, "help-check-list")}
      </section>
    ` : ""}

    <section class="help-topic-card">
      <h3>Useful commands and actions</h3>
      <div class="copy-command-list">
        ${(topic.commands || []).map((command) => `
          <button class="copy-command" data-copy-command="${escapeHtml(command)}">
            <code>${escapeHtml(command)}</code>
            <span>Copy</span>
          </button>
        `).join("")}
      </div>
    </section>

    <section class="help-topic-card">
      <h3>Useful links</h3>
      <ul class="detail-list">
        <li><a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer">Ollama model library</a></li>
        <li><a href="https://github.com/Small-ed1/local-llm-tooling-showcase" target="_blank" rel="noopener noreferrer">Project repository</a></li>
      </ul>
    </section>
  `;

  nav.querySelectorAll("[data-help-topic]").forEach((button) => {
    button.addEventListener("click", () => {
      nav.querySelectorAll("button").forEach((candidate) => {
        candidate.classList.toggle("active", candidate === button);
      });
      renderHelp();
    });
  });

  body.querySelectorAll("[data-copy-command]").forEach((button) => {
    button.addEventListener("click", async () => {
      await navigator.clipboard.writeText(button.dataset.copyCommand || "");
      const label = button.querySelector("span");
      if (!label) return;
      const original = label.textContent;
      label.textContent = "Copied";
      window.setTimeout(() => {
        label.textContent = original || "Copy";
      }, 900);
    });
  });
}

function applyModeVisibility() {
  const userMode = state.settings.mode === "user";

  document.body.classList.toggle("user-mode", userMode);

  document.querySelectorAll(".dev-only").forEach((node) => {
    node.hidden = userMode;
  });

  document
    .querySelectorAll('[data-page-target="tools"], [data-page-target="journal"], [data-dev-sidebar-section]')
    .forEach((node) => {
      node.hidden = userMode;
      node.setAttribute("aria-hidden", String(userMode));
      if (userMode && node.classList.contains("active")) {
        node.classList.remove("active");
      }
    });

  if (userMode && ["tools", "journal"].includes(state.activePage)) {
    setActivePage("chat", { closeDrawer: false });
  }
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

function settingValue(id, fallback = "") {
  return $(id)?.value ?? fallback;
}

function settingChecked(id, fallback = false) {
  return $(id)?.checked ?? fallback;
}

function settingNumber(id, fallback, min = -Infinity, max = Infinity) {
  const raw = Number(settingValue(id, fallback));
  const value = Number.isFinite(raw) ? raw : fallback;
  return Math.max(min, Math.min(max, value));
}

function readBehaviorSettingsFromModal() {
  state.settings.mode = $("settingsModeSelect")?.value || state.settings.mode || "dev";
  state.settings.density = $("settingsDensitySelect")?.value || state.settings.density || "comfortable";

  state.settings.stream = $("settingsStreamToggle")?.checked ?? state.settings.stream;
  state.settings.confirm = $("settingsConfirmToggle")?.checked ?? state.settings.confirm;
  state.settings.attachMemories = $("settingsMemoryToggle")?.checked ?? state.settings.attachMemories;
  state.settings.autoScroll = $("settingsAutoScrollToggle")?.checked ?? state.settings.autoScroll;
  state.settings.deepResearch = {
    mode: ["local", "hybrid"].includes($("settingsResearchModeSelect")?.value) ? $("settingsResearchModeSelect").value : DEFAULT_SETTINGS.deepResearch.mode,
    depth: settingNumber("settingsResearchDepthSelect", DEFAULT_SETTINGS.deepResearch.depth, 1, 4)
  };

  state.settings.openThinking = $("settingsOpenThinkingToggle")?.checked ?? state.settings.openThinking;
  state.settings.detailsEnabled = $("settingsDetailsToggle")?.checked ?? state.settings.detailsEnabled;
  state.settings.compactTools = $("settingsCompactToolsToggle")?.checked ?? state.settings.compactTools;

  state.settings.journalLimit = Math.max(5, Number($("settingsJournalLimit")?.value) || state.settings.journalLimit || 50);
  state.settings.messageWidth = Math.max(
    52,
    Math.min(120, Number($("settingsMessageWidth")?.value) || state.settings.messageWidth || 78)
  );

  state.settings.runtimeTimeouts = {
    ollama: settingNumber("settingsOllamaTimeout", state.settings.runtimeTimeouts?.ollama || DEFAULT_SETTINGS.runtimeTimeouts.ollama, 1, 3600),
    tools: settingNumber("settingsToolTimeout", state.settings.runtimeTimeouts?.tools || DEFAULT_SETTINGS.runtimeTimeouts.tools, 1, 3600)
  };
}

function commitBehaviorSettingsFromModal() {
  readBehaviorSettingsFromModal();
  applySettingsToMainControls();
  applyModeVisibility();
  updatePageChrome();
  renderRuntimeStatus();
  persist({ syncControls: false });
}

function saveSettings() {
  const selectedModel = settingValue("settingsModelSelect", $("modelSelect")?.value || "");

  if ($("modelSelect")) {
    $("modelSelect").value = selectedModel;
  }

  readBehaviorSettingsFromModal();

  state.settings.theme = readThemeFromControls(state.settings.theme);

  state.settings.memoryPrefix = settingValue("settingsMemoryPrefix", state.settings.memoryPrefix || DEFAULT_SETTINGS.memoryPrefix).trim() || DEFAULT_SETTINGS.memoryPrefix;
  state.settings.responseFormat = settingValue("settingsResponseFormat", state.settings.responseFormat || "");

  state.settings.runtimeTimeouts = {
    ollama: settingNumber("settingsOllamaTimeout", state.settings.runtimeTimeouts?.ollama || DEFAULT_SETTINGS.runtimeTimeouts.ollama, 1, 3600),
    tools: settingNumber("settingsToolTimeout", state.settings.runtimeTimeouts?.tools || DEFAULT_SETTINGS.runtimeTimeouts.tools, 1, 3600)
  };

  const nextOptions = {
    keep_alive: settingValue("settingsKeepAlive", state.settings.modelOptions?.keep_alive || "").trim(),
    stop: settingValue("settingsStopSequences", Array.isArray(state.settings.modelOptions?.stop) ? state.settings.modelOptions.stop.join("\n") : "")
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
  };

  MODEL_NUMERIC_OPTION_KEYS.forEach((key) => {
    const input = $(`settingsModel_${key}`);
    if (input) nextOptions[key] = Number(input.value);
    else if (state.settings.modelOptions && key in state.settings.modelOptions) nextOptions[key] = state.settings.modelOptions[key];
    else nextOptions[key] = DEFAULT_SETTINGS.modelOptions[key];
  });

  MODEL_BOOLEAN_OPTION_KEYS.forEach((key) => {
    const input = $(`settingsModel_${key}`);
    if (input) nextOptions[key] = input.checked;
    else if (state.settings.modelOptions && key in state.settings.modelOptions) nextOptions[key] = state.settings.modelOptions[key];
    else nextOptions[key] = DEFAULT_SETTINGS.modelOptions[key];
  });

  state.settings.modelOptions = nextOptions;

  if ($("settingsPromptSelect")) {
    state.activeSystemPromptId = $("settingsPromptSelect").value || null;
  }

  if (
    $("systemPromptTitleInput")?.value.trim() ||
    $("settingsSystemPromptInput")?.value.trim()
  ) {
    saveSystemPromptFromEditor({ persistNow: false });
  }

  state.profile = sanitizeProfile({
    name: settingValue("profileNameInput", state.profile.name || "").trim(),
    nickname: settingValue("profileNicknameInput", state.profile.nickname || "").trim(),
    about: settingValue("profileAboutInput", state.profile.about || "").trim(),
    preferences: settingValue("profilePreferencesInput", state.profile.preferences || "").trim(),
    other: settingValue("profileOtherInput", state.profile.other || "").trim(),
    userAvatar: state.profile.userAvatar || "",
    assistantAvatar: state.profile.assistantAvatar || ""
  });

  if ($("systemPromptInput")) {
    $("systemPromptInput").value = activeSystemPrompt()?.fullPrompt || "";
  }

  applySettingsToMainControls();
  updateModelMeta();
  applyModeVisibility();
  renderRuntimeStatus();
  persist({ syncControls: false });
  renderAll();
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
  $("saveSettingsBtn")?.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    saveSettings();
  });
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
  $("presetSystemPromptBtn")?.addEventListener("click", loadSystemPromptPreset);
  $("importSystemPromptBtn")?.addEventListener("click", () => $("systemPromptImportInput")?.click());
  $("exportSystemPromptBtn")?.addEventListener("click", exportSystemPrompts);
  $("systemPromptImportInput")?.addEventListener("change", (event) => readImportFile(event.target.files?.[0], importSystemPrompt));
  $("importProfileBtn")?.addEventListener("click", () => $("profileImportInput")?.click());
  $("exportProfileBtn")?.addEventListener("click", () => downloadJson("showcase-profile.json", state.profile));
  $("profileImportInput")?.addEventListener("change", (event) => readImportFile(event.target.files?.[0], importProfile));
  $("importMemoriesBtn")?.addEventListener("click", () => $("memoriesImportInput")?.click());
  $("exportMemoriesBtn")?.addEventListener("click", () => downloadJson("showcase-memories.json", { exportedAt: new Date().toISOString(), memories: state.memories }));
  $("memoriesImportInput")?.addEventListener("change", (event) => readImportFile(event.target.files?.[0], importMemories));
  $("themePresetSelect")?.addEventListener("change", (event) => applyThemePreset(event.target.value));
  $("profileUserAvatarInput")?.addEventListener("change", (event) => handleAvatarUpload("user", event.target.files?.[0]));
  $("profileAssistantAvatarInput")?.addEventListener("change", (event) => handleAvatarUpload("assistant", event.target.files?.[0]));
  [...THEME_COLOR_FIELDS.map(({ key }) => themeInputId(key)), "themeFontSelect"].forEach((id) => {
    $(id)?.addEventListener("input", () => {
      if ($("themePresetSelect")) $("themePresetSelect").value = "";
      state.settings.theme = readThemeFromControls(state.settings.theme);
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
  document.addEventListener("click", (event) => {
    if (event.target.closest(".session-menu")) return;
    document.querySelectorAll(".session-menu[open]").forEach((menu) => { menu.open = false; });
  });
}

function bindBehaviorSettingsAutosave() {
  const behaviorControlIds = new Set([
    "settingsModeSelect",
    "settingsDensitySelect",
    "settingsStreamToggle",
    "settingsConfirmToggle",
    "settingsMemoryToggle",
    "settingsAutoScrollToggle",
    "settingsOpenThinkingToggle",
    "settingsDetailsToggle",
    "settingsCompactToolsToggle",
    "settingsJournalLimit",
    "settingsMessageWidth",
    "settingsOllamaTimeout",
    "settingsToolTimeout"
  ]);

  document.addEventListener("change", (event) => {
    const target = event.target;
    if (!target || !behaviorControlIds.has(target.id)) return;
    commitBehaviorSettingsFromModal();
  });

  document.addEventListener("input", (event) => {
    const target = event.target;
    if (!target || !behaviorControlIds.has(target.id)) return;
    commitBehaviorSettingsFromModal();
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

function downloadText(filename, text, type = "text/plain") {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function readImportFile(file, handler) {
  if (!file) return;
  const reader = new FileReader();
  reader.addEventListener("load", () => handler(String(reader.result || ""), file));
  reader.readAsText(file);
}

function parseImportText(text) {
  try { return JSON.parse(text); } catch { return text; }
}

function importSystemPrompt(text, file) {
  const parsed = parseImportText(text);
  const items = Array.isArray(parsed) ? parsed : [parsed];
  items.forEach((item) => {
    const prompt = typeof item === "object" && item
      ? { title: item.title || file.name, shortMessage: item.shortMessage || item.short_message || "Imported prompt", context: item.context || "", fullPrompt: item.fullPrompt || item.full_prompt || item.prompt || item.content || text }
      : { title: file.name, shortMessage: "Imported text prompt", context: "", fullPrompt: String(item || text) };
    state.systemPrompts.unshift({ id: uid("prompt"), ...prompt, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() });
  });
  state.activeSystemPromptId = state.systemPrompts[0]?.id || null;
  persist();
  syncSettingsModal();
}

function exportSystemPrompts() {
  downloadJson("showcase-system-prompts.json", { exportedAt: new Date().toISOString(), activeSystemPromptId: state.activeSystemPromptId, systemPrompts: state.systemPrompts });
}

function loadSystemPromptPreset() {
  const label = SYSTEM_PROMPT_PRESETS.map((preset, index) => `${index + 1}. ${preset.title}`).join("\n");
  const choice = Number(prompt(`Choose a system prompt preset:\n${label}`, "1"));
  const preset = SYSTEM_PROMPT_PRESETS[choice - 1];
  if (!preset) return;
  state.systemPrompts.unshift({ id: uid("prompt"), ...preset, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() });
  state.activeSystemPromptId = state.systemPrompts[0].id;
  persist();
  syncSettingsModal();
}

function importProfile(text) {
  const parsed = parseImportText(text);
  if (typeof parsed === "object" && parsed) state.profile = sanitizeProfile({ ...state.profile, ...(parsed.profile || parsed) });
  else state.profile = sanitizeProfile({ ...state.profile, about: String(parsed || "") });
  persist();
  syncSettingsModal();
}

function importMemories(text, file) {
  const parsed = parseImportText(text);
  const source = Array.isArray(parsed) ? parsed : Array.isArray(parsed?.memories) ? parsed.memories : [parsed];
  const imported = source.map((item) => typeof item === "object" && item
    ? { id: item.id || uid("memory"), title: item.title || item.key || file.name, text: item.text || item.value || item.content || JSON.stringify(item), pinned: Boolean(item.pinned), createdAt: item.createdAt || new Date().toISOString() }
    : { id: uid("memory"), title: file.name, text: String(item || ""), pinned: false, createdAt: new Date().toISOString() }
  ).filter((item) => item.text.trim());
  state.memories = [...imported, ...state.memories];
  persist();
  renderMemories();
  syncSettingsModal();
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
  [...Object.values(STORAGE_KEYS), ...LEGACY_STORAGE_KEYS].forEach((key) => localStorage.removeItem(key));
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
  $("modelPanel").addEventListener("dblclick", () => openModelDetail($("modelSelect").value));
  $("sessionsPanel").addEventListener("dblclick", () => openSessionDetail(activeSession()));
  $("memoriesPanel").addEventListener("dblclick", () => openCollectionDetail("Memories", `${state.memories.length} local browser memories.`, state.memories));
  $("toolsPanel").addEventListener("dblclick", () => openCollectionDetail("Tools", `${state.tools.length} available tools.`, { tools: state.tools, tool_cards: state.toolCards }));
  $("adaptersPanel")?.addEventListener("dblclick", () => openCollectionDetail("Adapters", `${state.adapters.length} workspace adapters loaded.`, state.adapters));
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
  document.addEventListener("click", (event) => {
    const pageButton = event.target.closest("[data-page-target]");
    if (!pageButton) return;

    const pageName = pageButton.dataset.pageTarget;
    if (!PAGE_META[pageName]) return;

    event.preventDefault();
    event.stopPropagation();

    setActivePage(pageName);

    if (window.matchMedia("(max-width: 760px)").matches) {
      closeMobileDrawers();
    }
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
  $("composerFileBtn")?.addEventListener("click", () => $("composerFileInput")?.click());
  $("composerFileInput")?.addEventListener("change", insertComposerFiles);
  $("composerMoreBtn")?.addEventListener("click", toggleComposerMoreMenu);
  $("deepResearchBtn")?.addEventListener("click", toggleComposerDeepResearch);
  $("composerSystemPromptBtn")?.addEventListener("click", () => { toggleComposerMoreMenu(false); const box = $("systemPromptInput"); box.hidden = !box.hidden; if (!box.hidden) box.focus(); });
  $("composerClearBtn")?.addEventListener("click", () => { toggleComposerMoreMenu(false); clearActiveSession(); });
  $("composerSettingsBtn")?.addEventListener("click", () => { toggleComposerMoreMenu(false); openSettings(); });
  ["composerResearchDepthSelect", "composerResearchModeSelect"].forEach((id) => $(id)?.addEventListener("change", () => {
    const options = selectedDeepResearchOptions();
    setRequestStats(`deep research ready · ${options.mode} · depth ${options.depth}`);
  }));
  $("newSessionBtn").addEventListener("click", () => createSession(true));
  $("sidebarNewChatBtn")?.addEventListener("click", (event) => { event.stopPropagation(); createSession(true); });
  $("sidebarCollapseBtn")?.addEventListener("click", (event) => { event.stopPropagation(); toggleSidebarCollapsed(); });
  wireSidebarSearch();
  wireSidebarSessionMenu();
  $("addMemoryBtn").addEventListener("click", addMemory);
  $("clearBtn")?.addEventListener("click", clearActiveSession);
  $("refreshAdaptersBtn")?.addEventListener("click", loadAdapters);
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
    const control = $(id);
    if (!control) return;
    control.addEventListener("change", persist);
    control.addEventListener("input", persist);
  });
  bindModalChrome();
  bindBehaviorSettingsAutosave();
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

function toggleComposerMoreMenu(force = null) {
  const menu = $("composerMoreMenu");
  if (!menu) return;
  menu.hidden = force === null ? !menu.hidden : !force;
}

function toggleComposerDeepResearch() {
  state.composerDeepResearch = !state.composerDeepResearch;
  const panel = $("deepResearchPanel");
  const button = $("deepResearchBtn");
  if (panel) panel.hidden = !state.composerDeepResearch;
  if (button) {
    button.classList.toggle("active", state.composerDeepResearch);
    button.setAttribute("aria-pressed", String(state.composerDeepResearch));
  }
  if (state.composerDeepResearch) {
    const options = selectedDeepResearchOptions();
    setRequestStats(`deep research ready · ${options.mode} · depth ${options.depth}`);
  } else {
    setRequestStats("idle");
  }
}

function insertComposerFiles(event) {
  const files = Array.from(event.target.files || []);
  if (!files.length) return;
  files.forEach((file) => {
    readImportFile(file, (text) => {
      appendPrompt(`File: ${file.name}\n\n${text}`);
      setRequestStats(`inserted ${file.name}`);
    });
  });
  event.target.value = "";
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
  await Promise.allSettled([loadModels(), loadTools(), loadJournal(), loadRuntime()]);
  renderAll();
}

boot();


/* ===== Research Lab sidecar ===== */

async function researchApi(path, payload = null) {
  const options = payload
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }
    : { method: "GET" };
  const res = await fetch(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.ok === false) throw new Error(data.error || `Research API failed with HTTP ${res.status}`);
  return data;
}
