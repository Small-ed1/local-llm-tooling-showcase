from tooling_showcase.catalog import (
    render_group_usage,
    render_tool_hierarchy,
    render_tool_usage,
    select_tool_docs,
    select_tool_groups,
)


def test_catalog_renders_compact_hierarchy_and_detailed_usage():
    hierarchy = render_tool_hierarchy()
    assert "File:" in hierarchy
    assert "Git:" in hierarchy

    usage = render_tool_usage(["read_file", "git_status"])
    assert "read_file" in usage
    assert "path: relative file path" in usage
    assert "git_status()" in usage

    groups = render_group_usage(["filesystem", "git"])
    assert "search/read/write" in groups
    assert "status/diff/log" in groups


def test_catalog_selectors_match_short_queries():
    tool_ids = select_tool_docs("find the readme file and inspect it")
    assert "file_search" in tool_ids or "read_file" in tool_ids

    group_ids = select_tool_groups("check git status and commit history")
    assert "git" in group_ids
