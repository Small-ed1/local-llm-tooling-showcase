from tooling_showcase.cli import build_parser


def test_serve_commands_default_to_loopback():
    parser = build_parser()

    serve = parser.parse_args(["serve"])
    wrapper = parser.parse_args(["serve-ollama"])

    assert serve.host == "127.0.0.1"
    assert wrapper.host == "127.0.0.1"


def test_lan_binding_requires_explicit_host():
    parser = build_parser()

    serve = parser.parse_args(["serve", "--host", "0.0.0.0"])

    assert serve.host == "0.0.0.0"
