(function (global) {
  "use strict";

  const TOOL_EXAMPLES = {};
  const TOOL_DOCS = {};

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
    "local_doc_search",
    "local_doc_read",
    "query_index",
    "read_file",
    "list_memories",
    "load_memory",
    "save_memory",
    "tool_structure",
    "tree_view",
    "web_search"
  ]);

  const TOOL_PRESETS = [
    { id: "inspect_repo", label: "Inspect repo", tool: "tree_view", args: { path: ".", max_depth: 4 } },
    { id: "read_readme", label: "Read README", tool: "read_file", args: { path: "README.md" } },
    { id: "search_docs", label: "Search docs", tool: "local_doc_search", args: { query: "release checks", limit: 10 } },
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
        "node --check src/tooling_showcase/static/app-data.js",
        "node --check src/tooling_showcase/static/markdown.js",
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
            "Shell execution is guarded. Common command shapes are parsed for risky executables and destructive argument patterns, with raw-pattern checks kept as a fallback.",
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
            "Run node --check on each static JavaScript file first. Then run the optional browser smoke test or smoke test the page manually. This project has no frontend build step, so syntax checks and browser testing matter more.",
            "If CSS behaves strangely, look for duplicate breakpoint rules, stale old stylesheets, and hidden elements that are still taking layout space."
          ]
        }
      ],
      checklist: [
        "Run tooling-showcase doctor.",
        "Run node --check on each static JavaScript file.",
        "Run the browser smoke test when Playwright Chromium is installed.",
        "Check missing static files in browser devtools.",
        "Check /api/runtime.",
        "Check Ollama with ollama list.",
        "Inspect the journal in developer mode.",
        "Export state before clearing browser storage."
      ],
      commands: [
        "tooling-showcase doctor",
        "tooling-showcase doctor --json",
        "node --check src/tooling_showcase/static/app-data.js",
        "node --check src/tooling_showcase/static/markdown.js",
        "node --check src/tooling_showcase/static/app.js",
        "pytest tests/test_browser_smoke.py",
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

  global.ShowcaseData = Object.freeze({
    TOOL_EXAMPLES,
    TOOL_DOCS,
    PLANNER_SAFE_TOOLS,
    TOOL_PRESETS,
    THEME_COLOR_FIELDS,
    DEFAULT_THEME,
    THEME_PRESETS,
    SYSTEM_PROMPT_PRESETS,
    MODEL_NUMERIC_OPTION_KEYS,
    MODEL_BOOLEAN_OPTION_KEYS,
    MODEL_OPTION_GROUPS,
    MODEL_OPTION_LABELS,
    HELP_TOPICS,
    ROUTE_PATTERNS,
    DEFAULT_SETTINGS,
    DEFAULT_PROFILE,
    PAGE_META,
    STORAGE_KEYS,
    LEGACY_STORAGE_KEYS,
    MAX_SETTINGS_TEXT_CHARS,
    MAX_PREFIX_CHARS,
    MAX_PROFILE_TEXT_CHARS,
    MAX_AVATAR_DIMENSION,
    MAX_AVATAR_DATA_URL_CHARS,
    LOCAL_STORAGE_SCHEMA_VERSION,
    CHAT_CONTEXT_MAX_MESSAGES,
    CHAT_CONTEXT_MAX_CHARS
  });
})(globalThis);
