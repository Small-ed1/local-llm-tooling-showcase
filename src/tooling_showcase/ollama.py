from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

from tooling_showcase.config import OllamaConfig
from tooling_showcase.models import ActionResult


class OllamaClient:
    def __init__(self, config: OllamaConfig) -> None:
        self.config = config

    def ask(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_format: str | dict | None = None,
        model: str | None = None,
        options: dict | None = None,
        stream: bool = False,
        think: bool = False,
    ) -> ActionResult:
        if not self.config.enabled:
            return ActionResult(False, "Local Ollama fallback is disabled.")
        selected_model = _normalize_model_choice(model) or self.config.model
        payload = {
            "model": selected_model,
            "stream": stream,
            "think": think,
            "messages": [
                {
                    "role": "system",
                    "content": self._compose_system_prompt(system_prompt),
                },
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": self.config.temperature},
        }
        if options:
            payload["options"].update(options)
        if response_format is not None:
            payload["format"] = response_format
        data = json.dumps(payload).encode("utf-8")

        request = Request(
            self.config.endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        if stream:
            return self._stream_request(request)

        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if think and exc.code == 400 and "does not support thinking" in body.lower():
                return self.ask(
                    prompt,
                    system_prompt=system_prompt,
                    response_format=response_format,
                    model=model,
                    options=options,
                    stream=stream,
                    think=False,
                )
            return ActionResult(False, f"Ollama HTTP {exc.code}: {body}")
        except URLError as exc:
            return ActionResult(False, f"Failed to reach Ollama: {exc}")
        except TimeoutError as exc:
            return ActionResult(False, f"Timed out waiting for Ollama: {exc}")
        except OSError as exc:
            return ActionResult(False, f"Ollama request failed: {exc}")
        message = raw.get("message", {}) or {}
        content = str(message.get("content", "")).strip()
        thinking = str(message.get("thinking", "")).strip()
        if not content:
            return ActionResult(False, "Ollama returned an empty response.", data=raw)
        raw["thinking"] = thinking
        return ActionResult(True, content, data=raw)

    def _stream_request(self, request: Request) -> ActionResult:
        try:
            response = urlopen(request, timeout=self.config.timeout_seconds)
            chunks: list[str] = []
            while True:
                chunk = response.read(4096)
                if not chunk:
                    break
                text = chunk.decode("utf-8")
                for line in text.strip().split("\n"):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            chunks.append(content)
                    except json.JSONDecodeError:
                        continue
            full_content = "".join(chunks)
            if not full_content:
                return ActionResult(False, "Ollama streaming returned empty.")
            return ActionResult(True, full_content)
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return ActionResult(False, f"Ollama HTTP {exc.code}: {body}")
        except URLError as exc:
            return ActionResult(False, f"Failed to reach Ollama: {exc}")
        except TimeoutError as exc:
            return ActionResult(False, f"Timed out waiting for Ollama: {exc}")
        except OSError as exc:
            return ActionResult(False, f"Ollama request failed: {exc}")

    def _compose_system_prompt(self, system_prompt: str | None) -> str:
        if system_prompt:
            return system_prompt + "\n\n" + self.config.system_prompt
        return self.config.system_prompt


def _normalize_model_choice(model: str | None) -> str | None:
    if model is None:
        return None
    value = str(model).strip()
    if not value or value.lower() in {"none", "null", "auto", "default"}:
        return None
    return value
