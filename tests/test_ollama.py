from tooling_showcase.config import OllamaConfig
from tooling_showcase.ollama import OllamaClient


def test_ollama_payload_stabilization_clamps_runtime_options():
    client = OllamaClient(OllamaConfig())

    payload = client._stabilize_payload(
        {
            "think": False,
            "format": "json",
            "options": {
                "temperature": 0.9,
                "num_predict": 5000,
                "enable_thinking": True,
            },
        }
    )

    assert payload["think"] is True
    assert payload["format"] == "json"
    assert payload["options"]["temperature"] == 0.9
    assert payload["options"]["num_ctx"] == 4096
    assert payload["options"]["num_batch"] == 128
    assert payload["options"]["num_gpu"] == -1
    assert payload["options"]["main_gpu"] == 0
    assert payload["options"]["num_thread"] == 6
    assert payload["options"]["num_predict"] == 5000
    assert "enable_thinking" not in payload["options"]


def test_ollama_payload_stabilization_preserves_runtime_overrides():
    client = OllamaClient(OllamaConfig())

    payload = client._stabilize_payload(
        {
            "think": False,
            "options": {
                "num_ctx": 8192,
                "num_batch": 64,
                "num_gpu": 2,
                "main_gpu": 1,
                "num_thread": 12,
                "num_predict": -1,
            },
        }
    )

    assert payload["options"]["num_ctx"] == 8192
    assert payload["options"]["num_batch"] == 64
    assert payload["options"]["num_gpu"] == 2
    assert payload["options"]["main_gpu"] == 1
    assert payload["options"]["num_thread"] == 12
    assert payload["options"]["num_predict"] == -1


def test_ollama_payload_stabilization_preserves_explicit_thinking():
    client = OllamaClient(OllamaConfig())

    payload = client._stabilize_payload({"think": True, "options": {"num_predict": 128}})

    assert payload["think"] is True
    assert payload["options"]["num_predict"] == 128


def test_ollama_payload_stabilization_removes_option_think_alias():
    client = OllamaClient(OllamaConfig())

    payload = client._stabilize_payload({"think": False, "options": {"think": True}})

    assert payload["think"] is True
    assert "think" not in payload["options"]
