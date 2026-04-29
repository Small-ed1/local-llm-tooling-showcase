from tooling_showcase.router import IntentRouter


def test_router_matches_file_search():
    decision = IntentRouter().route("find file README")
    assert decision.action == "file_search"


def test_router_falls_back_to_llm():
    decision = IntentRouter().route("how should a local assistant choose tools")
    assert decision.route == "llm_fallback"
    assert decision.action is None


def test_router_matches_adapter_inventory():
    decision = IntentRouter().route("show adapters")
    assert decision.action == "adapter_inventory"


def test_router_matches_repo_investigation_and_compare_phrasing():
    inspect_decision = IntentRouter().route("figure out this codebase")
    assert inspect_decision.action == "tree_view"

    compare_decision = IntentRouter().route(
        "look online and compare this repo to ollama wrappers"
    )
    assert compare_decision.action == "web_search"


def test_router_matches_weather_and_kernel_phrasing():
    weather = IntentRouter().route("what's the weather in London tonight")
    assert weather.action == "weather_lookup"

    kernel = IntentRouter().route("what is the latest linux kernel stable version")
    assert kernel.action == "latest_linux_kernel"
