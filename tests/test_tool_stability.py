from tooling_showcase.server import _tool_cards


def test_tool_cards_mark_stability():
    cards = {card["id"]: card for card in _tool_cards(["read_file", "write_file", "draft_system_prompt"])}

    assert cards["read_file"]["stability"] == "stable"
    assert cards["draft_system_prompt"]["stability"] == "stable"
    assert cards["write_file"]["stability"] == "experimental"
