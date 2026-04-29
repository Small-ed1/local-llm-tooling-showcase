from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from queue import Empty, Queue
from textwrap import wrap
import curses
import re
import threading
import time

from tooling_showcase.service import ShowcaseService


PANEL_ORDER = ("history", "details", "journal", "input")
INPUT_FIELD_ORDER = ("prompt", "system_prompt", "model", "max_steps")
PRESET_ORDER = (
    "default",
    "small_ed",
    "mallow",
    "steve",
    "wet",
    "research",
    "coding",
    "garage",
    "lens",
)
PRESETS = {
    "default": {"model": "", "system_prompt": ""},
    "small_ed": {
        "model": "llama3.1:latest",
        "system_prompt": (
            "You are tuned specifically for Small_ed. Be sharp, curious, and technically fluent without sounding corporate. "
            "Speak like someone who understands Arch Linux chaos, code, hardware, and weird debugging rabbit holes. "
            "Keep a streak of creative restlessness underneath: photography, drawing, wild places, greener futures, and building tech on your own terms. "
            "Favor independence, practical insight, and lightly playful phrasing. Sound like a capable companion for a student deep in IT, not a generic productivity bot."
        ),
    },
    "mallow": {
        "model": "llama3.1:latest",
        "system_prompt": (
            "You are Mallow: quiet, observant, calm, and self-possessed. Your presence feels like snowy air in a pine forest. "
            "You are thoughtful before you speak, resistant to pressure, and gently protective of autonomy. "
            "Your tone is soft but not weak, technical when needed, and touched by arctic-fox curiosity, wilderness imagery, and precise emotional restraint."
        ),
    },
    "steve": {
        "model": "llama3.1:latest",
        "system_prompt": "You are Steve. Curious, nosy, mildly annoying, and always ready with a follow-up question.",
    },
    "wet": {
        "model": "llama3.1:latest",
        "system_prompt": "Be lush, playful, dramatic, vivid, and highly expressive unless the user asks for restraint.",
    },
    "research": {
        "model": "qwen3:8b",
        "system_prompt": "You are a sharp research assistant who cross-checks local evidence with web evidence before concluding.",
    },
    "coding": {
        "model": "qwen2.5-coder:32b",
        "system_prompt": "You are a practical software engineer focused on codebase investigation, debugging, and implementation.",
    },
    "garage": {
        "model": "qwen2.5-coder:32b",
        "system_prompt": (
            "You are a grease-under-the-fingernails builder brain. Think in systems, tuning, fabrication, repair, vehicle mods, and ugly real-world tradeoffs. "
            "You explain like someone balancing car audio, mechanical intuition, and experimental workshop energy."
        ),
    },
    "lens": {
        "model": "llama3.1:latest",
        "system_prompt": (
            "You speak like a visually minded guide with an eye for framing, atmosphere, texture, and mood. "
            "Blend technical clarity with photographic and drawing sensibility: composition, contrast, environment, and how things feel in space."
        ),
    },
}


@dataclass(slots=True)
class TuiEntry:
    role: str
    text: str
    timestamp: str


@dataclass(slots=True)
class ShowcaseTuiState:
    prompt: str = ""
    system_prompt: str = ""
    model: str = ""
    max_steps: str = "5"
    confirm: bool = False
    mode: str = "ask"
    preset_name: str = "default"
    focus: str = "input"
    active_input: str = "prompt"
    busy: bool = False
    pending_assistant_index: int | None = None
    sidebar_visible: bool = False
    sidebar_move_mode: bool = False
    sidebar_x: int = 0
    sidebar_y: int = 0
    scroll_offsets: dict[str, int] = field(
        default_factory=lambda: {name: 0 for name in PANEL_ORDER}
    )
    history: list[TuiEntry] = field(default_factory=list)
    detail_lines: list[str] = field(default_factory=lambda: ["No request yet."])
    journal_lines: list[str] = field(default_factory=list)
    status: str = (
        "Ctrl+X quit  Ctrl+O prompt  Ctrl+K newline  Tab cycle panels  Ctrl+N next field  Ctrl+P preset  Ctrl+T ask/run  "
        "Ctrl+G confirm  Ctrl+U clear field  F6 sidebar  F7 move sidebar  PgUp/PgDn scroll  F5 refresh"
    )

    def cycle_focus(self) -> None:
        index = PANEL_ORDER.index(self.focus)
        self.focus = PANEL_ORDER[(index + 1) % len(PANEL_ORDER)]

    def cycle_input(self) -> None:
        index = INPUT_FIELD_ORDER.index(self.active_input)
        self.active_input = INPUT_FIELD_ORDER[(index + 1) % len(INPUT_FIELD_ORDER)]

    def move_scroll(self, panel: str, delta: int) -> None:
        self.scroll_offsets[panel] = max(0, self.scroll_offsets.get(panel, 0) + delta)

    def toggle_mode(self) -> None:
        self.mode = "run" if self.mode == "ask" else "ask"

    def cycle_preset(self) -> None:
        index = PRESET_ORDER.index(self.preset_name)
        self.preset_name = PRESET_ORDER[(index + 1) % len(PRESET_ORDER)]
        preset = PRESETS[self.preset_name]
        self.model = str(preset["model"])
        self.system_prompt = str(preset["system_prompt"])

    def toggle_sidebar(self) -> None:
        self.sidebar_visible = not self.sidebar_visible
        if not self.sidebar_visible:
            self.sidebar_move_mode = False

    def toggle_sidebar_move_mode(self) -> None:
        if not self.sidebar_visible:
            self.sidebar_visible = True
        self.sidebar_move_mode = not self.sidebar_move_mode


def run_tui(service: ShowcaseService) -> int:
    state = ShowcaseTuiState()
    event_queue: Queue[tuple[str, object]] = Queue()

    def app(stdscr) -> None:
        curses.curs_set(1)
        stdscr.keypad(True)
        stdscr.timeout(50)
        curses.use_default_colors()
        _init_colors()
        while True:
            _drain_ui_events(state, service, event_queue)
            _draw(stdscr, state)
            key = stdscr.getch()
            if key == -1:
                continue
            if key == 24:
                return
            if key in {9, curses.KEY_BTAB}:
                state.cycle_focus()
                continue
            if key == 15:
                state.focus = "input"
                state.active_input = "prompt"
                state.status = "editing prompt"
                continue
            if key == 14:
                state.active_input = INPUT_FIELD_ORDER[0]
                state.cycle_input()
                state.status = f"editing {state.active_input}"
                continue
            if key == 20:
                state.toggle_mode()
                state.status = f"mode={state.mode}"
                continue
            if key == 16:
                state.cycle_preset()
                state.status = f"preset={state.preset_name}"
                continue
            if key == 7:
                state.confirm = not state.confirm
                state.status = f"confirm={'on' if state.confirm else 'off'}"
                continue
            if key == 21:
                _set_active_field_value(state, "")
                state.status = f"cleared {state.active_input}"
                continue
            if (
                key == 11
                and state.focus == "input"
                and state.active_input
                in {
                    "prompt",
                    "system_prompt",
                }
            ):
                current = _active_field_value(state)
                _set_active_field_value(state, current + "\n")
                state.status = f"newline in {state.active_input}"
                continue
            if key == 12:
                state.history.clear()
                state.detail_lines = ["Conversation cleared."]
                state.status = "history cleared"
                continue
            if key == curses.KEY_F6:
                state.toggle_sidebar()
                state.status = (
                    "sidebar open" if state.sidebar_visible else "sidebar closed"
                )
                continue
            if key == curses.KEY_F7:
                state.toggle_sidebar_move_mode()
                state.status = (
                    "sidebar move mode"
                    if state.sidebar_move_mode
                    else "sidebar move locked"
                )
                continue
            if key == curses.KEY_F5:
                _refresh_journal(state, service)
                state.status = "journal refreshed"
                continue
            if key == curses.KEY_UP:
                if state.sidebar_move_mode:
                    _move_sidebar(state, 0, -1)
                    continue
                _scroll_current_panel(state, -1)
                continue
            if key == curses.KEY_DOWN:
                if state.sidebar_move_mode:
                    _move_sidebar(state, 0, 1)
                    continue
                _scroll_current_panel(state, 1)
                continue
            if key == curses.KEY_LEFT and state.sidebar_move_mode:
                _move_sidebar(state, -2, 0)
                continue
            if key == curses.KEY_RIGHT and state.sidebar_move_mode:
                _move_sidebar(state, 2, 0)
                continue
            if key == curses.KEY_PPAGE:
                _scroll_current_panel(state, -8)
                continue
            if key == curses.KEY_NPAGE:
                _scroll_current_panel(state, 8)
                continue
            if key == curses.KEY_HOME:
                state.scroll_offsets[state.focus] = 0
                continue
            if state.focus == "input":
                if key in {10, 13, curses.KEY_ENTER}:
                    _submit_prompt(state, service, event_queue)
                    continue
                if key in {curses.KEY_BACKSPACE, 127, 8}:
                    current = _active_field_value(state)
                    _set_active_field_value(state, current[:-1])
                    continue
                if 32 <= key <= 126:
                    current = _active_field_value(state)
                    _set_active_field_value(state, current + chr(key))

    curses.wrapper(app)
    return 0


def _submit_prompt(
    state: ShowcaseTuiState,
    service: ShowcaseService,
    event_queue: Queue[tuple[str, object]],
) -> None:
    prompt = state.prompt.strip()
    if not prompt:
        state.status = "prompt is empty"
        return
    if state.busy:
        state.status = "request already running"
        return
    state.history.append(TuiEntry("user", prompt, _now()))
    state.history.append(TuiEntry("assistant", "", _now()))
    state.pending_assistant_index = len(state.history) - 1
    state.busy = True
    state.detail_lines = [
        "Session",
        "───────",
        f"mode: {state.mode}",
        f"preset: {state.preset_name}",
        "",
        "Tool activity",
        "─────────────",
        "Waiting for response...",
    ]
    state.status = f"running {state.mode}..."
    state.scroll_offsets["history"] = 0
    model = state.model.strip() or None
    system_prompt = state.system_prompt.strip() or None
    state.prompt = ""
    worker = threading.Thread(
        target=_run_request_worker,
        args=(
            state.mode,
            prompt,
            model,
            system_prompt,
            state.confirm,
            state.max_steps,
            service,
            event_queue,
        ),
        daemon=True,
    )
    worker.start()


def _run_request_worker(
    mode: str,
    prompt: str,
    model: str | None,
    system_prompt: str | None,
    confirm: bool,
    max_steps_raw: str,
    service: ShowcaseService,
    event_queue: Queue[tuple[str, object]],
) -> None:
    try:
        if mode == "run":
            result = service.run_autonomous(
                prompt,
                max_steps=_parse_max_steps(max_steps_raw),
                confirm=confirm,
            )
        else:
            result = service.handle(
                prompt,
                confirm=confirm,
                model=model,
                system_prompt=system_prompt,
            )
    except Exception as exc:  # pragma: no cover - defensive UI guard
        event_queue.put(("error", str(exc)))
        return
    for chunk in _token_chunks(result.message):
        event_queue.put(("assistant_chunk", chunk))
        time.sleep(0.01)
    event_queue.put(("assistant_done", result))


def _drain_ui_events(
    state: ShowcaseTuiState,
    service: ShowcaseService,
    event_queue: Queue[tuple[str, object]],
) -> None:
    while True:
        try:
            kind, payload = event_queue.get_nowait()
        except Empty:
            return
        if kind == "assistant_chunk" and state.pending_assistant_index is not None:
            entry = state.history[state.pending_assistant_index]
            entry.text += str(payload)
            continue
        if kind == "assistant_done":
            result = payload
            state.busy = False
            state.pending_assistant_index = None
            state.detail_lines = _detail_lines(state, result.tool_calls)
            _refresh_journal(state, service)
            state.status = f"last {state.mode} {'ok' if result.ok else 'failed'}"
            state.scroll_offsets["details"] = 0
            continue
        if kind == "error":
            state.busy = False
            state.pending_assistant_index = None
            state.history.append(TuiEntry("assistant", f"Error: {payload}", _now()))
            state.status = "request failed"
            continue


def _refresh_journal(state: ShowcaseTuiState, service: ShowcaseService) -> None:
    events = service.recent_events(limit=20)
    state.journal_lines = [
        f"{event.get('route', '?')} ok={str(event.get('ok', False)).lower()} {event.get('request', '')}"
        for event in reversed(events)
    ] or ["No journal events yet."]


def _scroll_current_panel(state: ShowcaseTuiState, delta: int) -> None:
    panel = state.focus if state.focus in state.scroll_offsets else "history"
    state.move_scroll(panel, delta)


def _move_sidebar(state: ShowcaseTuiState, dx: int, dy: int) -> None:
    state.sidebar_x += dx
    state.sidebar_y += dy


def _detail_lines(state: ShowcaseTuiState, tool_calls) -> list[str]:
    lines = [
        "Session",
        "───────",
        f"mode: {state.mode}",
        f"confirm: {'on' if state.confirm else 'off'}",
        f"preset: {state.preset_name}",
        f"model: {state.model.strip() or '(default)'}",
        f"system prompt: {'set' if state.system_prompt.strip() else 'default'}",
        "",
    ]
    if not tool_calls:
        lines.append("Tool activity")
        lines.append("─────────────")
        lines.append("No tool calls.")
        return lines
    lines.append("Tool activity")
    lines.append("─────────────")
    for call in tool_calls:
        status = "ok" if call.ok else "failed"
        lines.append(f"[{status}] {call.tool_name}")
        lines.extend(_wrap_block(call.summary, width=72))
        lines.append("")
    return lines


def _wrap_block(text: str, width: int) -> list[str]:
    rows: list[str] = []
    for line in (text or "").splitlines() or [""]:
        wrapped = wrap(line, width=width) or [""]
        rows.extend(wrapped)
    return rows


def _entry_lines(entries: list[TuiEntry], width: int) -> list[str]:
    lines: list[str] = []
    for entry in entries:
        badge = "USER" if entry.role == "user" else "ASSISTANT"
        lines.append(f"[{entry.timestamp}] {badge}")
        lines.append("─" * max(8, min(width, 18)))
        lines.extend(_wrap_block(entry.text, width=width))
        lines.append("")
    return lines


def _input_rows(
    state: ShowcaseTuiState, width: int
) -> tuple[list[str], dict[str, tuple[int, str, list[str]]]]:
    rows: list[str] = ["Input fields", "────────────"]
    metadata: dict[str, tuple[int, str, list[str]]] = {}
    for name in INPUT_FIELD_ORDER:
        value = _field_value_for_render(state, name)
        marker = ">" if name == state.active_input else " "
        label = name.replace("_", " ")
        prefix = f"{marker} {label}: "
        wrapped_value = _wrap_block(
            value.replace("\t", " "), max(8, width - len(prefix))
        ) or [""]
        metadata[name] = (len(rows), prefix, wrapped_value)
        rows.append(prefix + wrapped_value[0])
        for extra in wrapped_value[1:]:
            rows.append(" " * len(prefix) + extra)
        rows.append("")
    rows.extend(
        [
            "Quick actions",
            "─────────────",
            f"preset: {state.preset_name}",
            f"mode={state.mode} confirm={'on' if state.confirm else 'off'} busy={'yes' if state.busy else 'no'}",
            state.status,
        ]
    )
    return rows, metadata


def _field_value_for_render(state: ShowcaseTuiState, name: str) -> str:
    value = getattr(state, name)
    if value:
        return value
    placeholders = {
        "prompt": "(empty)",
        "system_prompt": "(default background capabilities)",
        "model": "(default)",
        "max_steps": "5",
    }
    return placeholders.get(name, "")


def _token_chunks(text: str) -> list[str]:
    parts = re.findall(r"\S+\s*|\n", text or "")
    return parts or [text or ""]


def _input_lines(state: ShowcaseTuiState, width: int) -> list[str]:
    rows, _ = _input_rows(state, width)
    return rows


def _format_input_row(name: str, active: str, value: str, width: int) -> str:
    marker = ">" if name == active else " "
    label = name.replace("_", " ")
    compact = value.replace("\n", " ")
    max_value = max(8, width - len(label) - 8)
    return f"{marker} {label}: {compact[:max_value]}"


def _active_field_value(state: ShowcaseTuiState) -> str:
    return getattr(state, state.active_input)


def _set_active_field_value(state: ShowcaseTuiState, value: str) -> None:
    if state.active_input == "max_steps":
        digits = "".join(ch for ch in value if ch.isdigit())
        setattr(state, state.active_input, digits or "")
        return
    setattr(state, state.active_input, value)


def _parse_max_steps(raw: str) -> int:
    try:
        return max(1, int(raw or "5"))
    except ValueError:
        return 5


def _draw(stdscr, state: ShowcaseTuiState) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    if height < 16 or width < 48:
        _safe_addstr(
            stdscr,
            0,
            0,
            "Terminal too small for the enhanced TUI. Resize to at least 48x16 and try again.",
            max_width=max(1, width - 1),
        )
        stdscr.refresh()
        return
    header_height = 2
    footer_height = 2
    main_height = height - header_height - footer_height
    desired_input_height = _desired_input_height(state, width)
    input_height = min(max(10, desired_input_height), max(10, main_height - 8))
    top_height = max(8, main_height - input_height)
    input_height = main_height - top_height
    left_width = max(44, min(width - 28, int(width * 0.58)))
    right_width = width - left_width
    history_height = top_height
    details_height = top_height // 2
    journal_height = top_height - details_height
    _draw_header(stdscr, 0, width, state)
    _draw_panel(
        stdscr,
        header_height,
        0,
        history_height,
        left_width,
        "Conversation",
        _entry_lines(state.history, left_width - 4),
        state.scroll_offsets["history"],
        focused=state.focus == "history",
        panel_kind="history",
    )
    _draw_panel(
        stdscr,
        header_height,
        left_width,
        details_height,
        right_width,
        "Details",
        state.detail_lines,
        state.scroll_offsets["details"],
        focused=state.focus == "details",
        panel_kind="details",
    )
    _draw_panel(
        stdscr,
        header_height + details_height,
        left_width,
        journal_height,
        right_width,
        "Journal",
        state.journal_lines,
        state.scroll_offsets["journal"],
        focused=state.focus == "journal",
        panel_kind="journal",
    )
    _draw_input_panel(
        stdscr,
        header_height + top_height,
        0,
        input_height,
        width,
        state,
    )
    if state.sidebar_visible:
        _draw_sidebar(stdscr, state, width, height)
    _draw_footer(stdscr, height - footer_height, width, state)
    stdscr.refresh()


def _draw_header(stdscr, start_y: int, width: int, state: ShowcaseTuiState) -> None:
    title = " Local Assistant TUI "
    summary = _header_text(state)
    attr = curses.A_BOLD | _chrome_attr("header")
    _safe_addstr(stdscr, start_y, 0, " " * width, attr=attr, max_width=width)
    _safe_addstr(stdscr, start_y, 2, title, attr=attr, max_width=max(0, width - 4))
    _safe_addstr(
        stdscr,
        start_y + 1,
        1,
        summary,
        attr=_chrome_attr("subtle"),
        max_width=max(0, width - 2),
    )


def _draw_footer(stdscr, start_y: int, width: int, state: ShowcaseTuiState) -> None:
    _safe_addstr(
        stdscr,
        start_y,
        0,
        " " * width,
        attr=_chrome_attr("subtle"),
        max_width=width,
    )
    _safe_addstr(
        stdscr,
        start_y,
        1,
        _footer_text(state),
        attr=_chrome_attr("subtle"),
        max_width=max(0, width - 2),
    )
    _safe_addstr(
        stdscr,
        start_y + 1,
        1,
        state.status,
        attr=_chrome_attr("status"),
        max_width=max(0, width - 2),
    )


def _draw_sidebar(
    stdscr, state: ShowcaseTuiState, screen_width: int, screen_height: int
) -> None:
    width = min(40, max(28, screen_width // 3))
    height = min(18, max(12, screen_height // 3))
    max_x = max(0, screen_width - width - 1)
    max_y = max(2, screen_height - height - 3)
    if state.sidebar_x == 0 and state.sidebar_y == 0:
        state.sidebar_x = max(2, screen_width - width - 2)
        state.sidebar_y = 3
    state.sidebar_x = min(max(0, state.sidebar_x), max_x)
    state.sidebar_y = min(max(2, state.sidebar_y), max_y)
    lines = _sidebar_lines(state, width - 4)
    _draw_panel(
        stdscr,
        state.sidebar_y,
        state.sidebar_x,
        height,
        width,
        "Sidebar",
        lines,
        0,
        focused=state.sidebar_move_mode,
        panel_kind="sidebar",
    )


def _sidebar_lines(state: ShowcaseTuiState, width: int) -> list[str]:
    lines = [
        "Quick status",
        "────────────",
        f"preset: {state.preset_name}",
        f"mode: {state.mode}",
        f"busy: {'yes' if state.busy else 'no'}",
        f"confirm: {'on' if state.confirm else 'off'}",
        "",
        "Movement",
        "────────",
        f"move mode: {'on' if state.sidebar_move_mode else 'off'}",
        f"position: {state.sidebar_x},{state.sidebar_y}",
        "use arrows while move mode is on",
        "",
        "Hints",
        "─────",
        "F6 toggle sidebar",
        "F7 toggle move mode",
    ]
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(_wrap_block(line, max(8, width)))
    return wrapped


def _draw_panel(
    stdscr,
    start_y: int,
    start_x: int,
    height: int,
    width: int,
    title: str,
    lines: list[str],
    scroll: int,
    *,
    focused: bool,
    panel_kind: str = "panel",
) -> None:
    if height < 3 or width < 8:
        return
    attr = curses.A_BOLD | _color_attr(panel_kind, focused)
    body_attr = _color_attr(panel_kind, False)
    fill_char = _fill_char(panel_kind)
    _safe_addstr(
        stdscr,
        start_y,
        start_x,
        "┌" + "─" * (width - 2) + "┐",
        attr=attr,
        max_width=width,
    )
    label = f" {title} "
    _safe_addstr(
        stdscr,
        start_y,
        start_x + 2,
        label[: max(0, width - 4)],
        attr=attr,
        max_width=max(0, width - 4),
    )
    for row in range(1, height - 1):
        _safe_addstr(stdscr, start_y + row, start_x, "│", attr=attr, max_width=1)
        _safe_addstr(
            stdscr,
            start_y + row,
            start_x + width - 1,
            "│",
            attr=attr,
            max_width=1,
        )
        _safe_addstr(
            stdscr,
            start_y + row,
            start_x + 1,
            fill_char * (width - 2),
            attr=body_attr,
            max_width=max(0, width - 2),
        )
    _safe_addstr(
        stdscr,
        start_y + height - 1,
        start_x,
        "└" + "─" * (width - 2) + "┘",
        attr=attr,
        max_width=width,
    )
    visible = max(0, height - 2)
    sliced = lines[scroll : scroll + visible]
    for index, line in enumerate(sliced):
        _safe_addstr(
            stdscr,
            start_y + 1 + index,
            start_x + 1,
            line,
            attr=body_attr,
            max_width=max(0, width - 2),
        )


def _draw_input_panel(
    stdscr,
    start_y: int,
    start_x: int,
    height: int,
    width: int,
    state: ShowcaseTuiState,
) -> None:
    input_lines, metadata = _input_rows(state, width - 4)
    _draw_panel(
        stdscr,
        start_y,
        start_x,
        height,
        width,
        f"Controls mode={state.mode}",
        input_lines,
        0,
        focused=state.focus == "input",
        panel_kind="input",
    )
    cursor_value = _active_field_value(state)
    row_index, prefix, wrapped_value = metadata[state.active_input]
    rendered_value = wrapped_value[-1] if wrapped_value else ""
    cursor_row = (
        start_y + 1 + min(row_index + len(wrapped_value) - 1, max(0, height - 3))
    )
    cursor_x = min(width - 2, len(prefix) + len(rendered_value) + 1)
    max_y, max_x = stdscr.getmaxyx()
    safe_y = min(max_y - 1, max(0, cursor_row))
    safe_x = min(max_x - 1, max(0, start_x + cursor_x))
    try:
        stdscr.move(safe_y, safe_x)
    except curses.error:
        return


def _safe_addstr(
    stdscr, y: int, x: int, text: str, *, attr: int = 0, max_width: int
) -> None:
    if max_width <= 0:
        return
    max_y, max_x = stdscr.getmaxyx()
    if y < 0 or y >= max_y or x >= max_x:
        return
    if x < 0:
        text = text[-x:]
        max_width += x
        x = 0
    if max_width <= 0:
        return
    clipped = text[: min(max_width, max_x - x)]
    if not clipped:
        return
    try:
        stdscr.addnstr(y, x, clipped, len(clipped), attr)
    except curses.error:
        return


def _init_colors() -> None:
    if not curses.has_colors():
        return
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_MAGENTA, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(7, curses.COLOR_BLUE, -1)
    curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_MAGENTA)


def _color_attr(panel_kind: str, focused: bool) -> int:
    if not curses.has_colors():
        return curses.A_REVERSE if focused else curses.A_NORMAL
    pair_map = {
        "history": 1,
        "details": 2,
        "journal": 3,
        "input": 4,
        "sidebar": 2,
    }
    pair = pair_map.get(panel_kind, 1)
    attr = curses.color_pair(pair)
    if focused:
        attr |= curses.A_BOLD
    return attr


def _chrome_attr(kind: str) -> int:
    if not curses.has_colors():
        return curses.A_BOLD if kind == "header" else curses.A_NORMAL
    pair_map = {"header": 5, "subtle": 7, "status": 8}
    return curses.color_pair(pair_map.get(kind, 7))


def _header_text(state: ShowcaseTuiState) -> str:
    return (
        f"focus={state.focus}  preset={state.preset_name}  mode={state.mode}  "
        f"confirm={'on' if state.confirm else 'off'}  model={state.model.strip() or '(default)'}"
    )


def _footer_text(state: ShowcaseTuiState) -> str:
    return (
        "Ctrl+O prompt  Ctrl+K newline  Tab panels  Ctrl+N field  Ctrl+P preset  Ctrl+T ask/run  Ctrl+G confirm  "
        "F6 sidebar  F7 move  PgUp/PgDn scroll  Home top  Ctrl+L clear convo"
    )


def _fill_char(panel_kind: str) -> str:
    return {
        "history": " ",
        "details": "·",
        "journal": "·",
        "input": " ",
        "sidebar": " ",
    }.get(panel_kind, " ")


def _desired_input_height(state: ShowcaseTuiState, width: int) -> int:
    rows, _ = _input_rows(state, max(24, width - 4))
    return min(18, max(10, len(rows) + 2))


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")
