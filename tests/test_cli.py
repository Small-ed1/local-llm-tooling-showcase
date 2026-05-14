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
    assert serve.enable_remote_tool_api is False


def test_serve_supports_remote_tool_api_opt_in():
    parser = build_parser()

    serve = parser.parse_args(["serve", "--host", "0.0.0.0", "--enable-remote-tool-api"])

    assert serve.host == "0.0.0.0"
    assert serve.enable_remote_tool_api is True


def test_doctor_command_supports_json_output():
    parser = build_parser()

    doctor = parser.parse_args(["doctor", "--json"])

    assert doctor.command == "doctor"
    assert doctor.json is True


def test_runtime_commands_support_timeout_options():
    parser = build_parser()

    ask = parser.parse_args(["ask", "hello", "--ollama-timeout", "240", "--tool-timeout", "45"])
    serve = parser.parse_args(["serve", "--ollama-timeout", "180", "--tool-timeout", "60"])
    wrapper = parser.parse_args(["serve-ollama", "--ollama-timeout", "300", "--tool-timeout", "90"])

    assert ask.ollama_timeout == 240
    assert ask.tool_timeout == 45
    assert serve.ollama_timeout == 180
    assert serve.tool_timeout == 60
    assert wrapper.ollama_timeout == 300
    assert wrapper.tool_timeout == 90
