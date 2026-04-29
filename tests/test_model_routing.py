from tooling_showcase.model_routing import model_profiles, route_model


def test_model_catalog_assigns_unique_jobs_to_remaining_models():
    profiles = model_profiles()
    models = {profile["model"] for profile in profiles}
    assert {
        "dolphin3:latest",
        "phi4:14b",
        "mistral-nemo:12b",
        "qwen2.5:14b-instruct",
        "qwen3:8b",
        "qwen3.5:9b",
        "nomic-embed-text:latest",
        "qwen2.5vl:7b",
        "embeddinggemma:latest",
        "llama3.2:latest",
    } <= models
    assert len({profile["job"] for profile in profiles}) == len(profiles)


def test_route_model_picks_expected_specialists():
    assert route_model("Fix this Python function and refactor the tests").profile.model == "qwen3.5:9b"
    assert route_model("Help debug my Arch Linux boot issue").profile.model == "mistral-nemo:12b"
    assert route_model("Summarize this long report briefly").profile.model == "dolphin3:latest"
    assert route_model("Roleplay as a companion character").profile.model == "phi4:14b"
    assert route_model("Analyze this screenshot and tell me what it shows").profile.model == "qwen2.5vl:7b"


def test_route_model_uses_general_default_for_everyday_requests():
    route = route_model("What should I cook tonight?")
    assert route.profile.model == "qwen3:8b"
    assert route.profile.category == "general"
