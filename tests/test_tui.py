from tooling_showcase.models import ToolCall
from tooling_showcase.tui import (
    INPUT_FIELD_ORDER,
    PANEL_ORDER,
    PRESET_ORDER,
    ShowcaseTuiState,
    _detail_lines,
    _entry_lines,
    _footer_text,
    _header_text,
    _input_lines,
    _move_sidebar,
    _parse_max_steps,
    _sidebar_lines,
    _set_active_field_value,
)


def test_tui_state_cycles_focus_scroll_and_input_fields():
    state = ShowcaseTuiState()
    assert state.focus == "input"
    seen = []
    for _ in range(len(PANEL_ORDER)):
        seen.append(state.focus)
        state.cycle_focus()
    assert tuple(seen) == ("input", "history", "details", "journal")

    seen_inputs = []
    for _ in range(len(INPUT_FIELD_ORDER)):
        seen_inputs.append(state.active_input)
        state.cycle_input()
    assert tuple(seen_inputs) == INPUT_FIELD_ORDER

    state.move_scroll("history", 3)
    state.move_scroll("history", -2)
    state.move_scroll("history", -10)
    assert state.scroll_offsets["history"] == 0

    state.toggle_sidebar()
    assert state.sidebar_visible is True
    state.toggle_sidebar_move_mode()
    assert state.sidebar_move_mode is True
    _move_sidebar(state, 3, 2)
    assert state.sidebar_x == 3
    assert state.sidebar_y == 2
    state.toggle_sidebar()
    assert state.sidebar_visible is False
    assert state.sidebar_move_mode is False


def test_tui_render_helpers_produce_lines():
    entries = _entry_lines([], 20)
    assert entries == []

    state = ShowcaseTuiState(
        prompt="inspect repo",
        system_prompt="You are Steve.",
        model="llama3.1:latest",
        max_steps="7",
        confirm=True,
        mode="ask",
    )
    detail_lines = _detail_lines(state, [ToolCall("read_file", True, "hello world")])
    assert detail_lines[0] == "Session"
    assert any("mode: ask" in line for line in detail_lines)
    assert any("[ok] read_file" in line for line in detail_lines)

    input_lines = _input_lines(state, 80)
    assert any("prompt:" in line for line in input_lines)
    assert any("system prompt:" in line for line in input_lines)
    assert any("model:" in line for line in input_lines)
    assert any("Input fields" in line for line in input_lines)
    assert "preset=default" in _header_text(state)
    assert "Ctrl+O prompt" in _footer_text(state)
    assert "F6 sidebar" in _footer_text(state)
    assert "Ctrl+P preset" in _footer_text(state)

    sidebar_lines = _sidebar_lines(state, 30)
    assert any("Quick status" in line for line in sidebar_lines)
    assert any("F6 toggle sidebar" in line for line in sidebar_lines)


def test_tui_numeric_input_and_mode_helpers():
    state = ShowcaseTuiState()
    state.active_input = "max_steps"
    _set_active_field_value(state, "12abc")
    assert state.max_steps == "12"
    assert _parse_max_steps(state.max_steps) == 12
    assert _parse_max_steps("") == 5
    assert _parse_max_steps("garbage") == 5

    state.toggle_mode()
    assert state.mode == "run"

    seen_presets = []
    for _ in range(len(PRESET_ORDER)):
        seen_presets.append(state.preset_name)
        state.cycle_preset()
    assert tuple(seen_presets) == PRESET_ORDER
    assert "small_ed" in PRESET_ORDER
    assert "mallow" in PRESET_ORDER
