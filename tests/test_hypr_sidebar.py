from tooling_showcase.hypr_sidebar import (
    _looks_like_desktop_control,
    build_planner_prompt,
    direct_plan,
    summarize_snapshot,
)


def test_direct_plan_matches_common_hypr_requests():
    assert (
        direct_plan("switch to workspace 3")["commands"][0]["dispatch"] == "workspace 3"
    )
    assert (
        direct_plan("move active window to workspace 5")["commands"][0]["dispatch"]
        == "movetoworkspace 5"
    )
    assert direct_plan("launch foot")["commands"][0]["dispatch"] == "exec foot"
    assert (
        direct_plan("toggle floating")["commands"][0]["dispatch"]
        == "togglefloating active"
    )


def test_prompt_builder_includes_hypr_snapshot():
    snapshot = {
        "workspaces": [{"id": 1, "name": "1", "windows": 2, "focused": True}],
        "clients": [
            {"title": "Firefox", "class": "firefox", "workspace": 1, "address": "0x123"}
        ],
        "active_window": {
            "title": "Firefox",
            "class": "firefox",
            "workspace": 1,
            "address": "0x123",
        },
    }
    prompt = build_planner_prompt("focus firefox", snapshot)
    assert "focus firefox" in prompt
    assert "Workspaces:" in prompt
    assert "Firefox" in prompt


def test_summarize_snapshot_formats_clients_and_workspaces():
    snapshot = {
        "workspaces": [{"id": 2, "name": "2", "windows": 1, "focused": False}],
        "clients": [
            {"title": "foot", "class": "foot", "workspace": 2, "address": "0xaaa"}
        ],
        "active_window": {
            "title": "foot",
            "class": "foot",
            "workspace": 2,
            "address": "0xaaa",
        },
    }
    summary = summarize_snapshot(snapshot)
    assert "id=2" in summary
    assert "title=foot" in summary


def test_desktop_control_detection_stays_out_of_general_queries():
    assert _looks_like_desktop_control("move active window to workspace 5") is True
    assert _looks_like_desktop_control("what's the latest linux kernel?") is False
    assert _looks_like_desktop_control("what is the weather in London tonight?") is False
