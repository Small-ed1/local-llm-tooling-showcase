from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from contextlib import contextmanager
import json
import threading
from typing import Iterator

from tooling_showcase.config import OllamaConfig
from tooling_showcase.models import ActionResult


class OllamaClient:
    def __init__(self, config: OllamaConfig) -> None:
        self.config = config
        self._request_lock = threading.Lock()

    def _stabilize_payload(self, payload: dict) -> dict:
        opts = dict(payload.get("options") or {})
        payload["think"] = bool(payload.get("think", False) or opts.get("enable_thinking", False) or opts.get("think", False))
        opts["num_ctx"] = 4096
        opts["num_batch"] = 128
        opts["num_gpu"] = -1
        opts["main_gpu"] = 0
        opts["num_thread"] = 6

        try:
            predict = int(opts.get("num_predict", 512))
        except (TypeError, ValueError):
            predict = 512
        if predict < 0 or predict > 512:
            predict = 512

        opts["num_predict"] = predict
        opts.pop("enable_thinking", None)
        opts.pop("think", None)
        payload["options"] = opts
        return payload

    @contextmanager
    def _locked_urlopen(self, *args, **kwargs):
        with self._request_lock:
            with urlopen(*args, **kwargs) as response:
                yield response


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
        timeout_seconds: int | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> ActionResult:
        if not self.config.enabled:
            return ActionResult(False, "Local Ollama fallback is disabled.")
        selected_model = _normalize_model_choice(model) or self.config.model
        payload = {
            "model": selected_model,
            "stream": stream,
            "think": think,
            "messages": self._compose_messages(prompt, system_prompt=system_prompt, messages=messages),
            "options": {"temperature": self.config.temperature},
        }
        if options:
            payload["options"].update(options)
        if response_format is not None:
            payload["format"] = response_format
        payload = self._stabilize_payload(payload)
        data = json.dumps(payload).encode("utf-8")

        request = Request(
            self.config.endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        if stream:
            return self._stream_request(request, timeout_seconds=timeout_seconds)

        try:
            with self._locked_urlopen(request, timeout=timeout_seconds or self.config.timeout_seconds) as response:
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
                    timeout_seconds=timeout_seconds,
                    messages=messages,
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

    def stream_events(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_format: str | dict | None = None,
        model: str | None = None,
        options: dict | None = None,
        think: bool = False,
        timeout_seconds: int | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> Iterator[dict]:
        if not self.config.enabled:
            yield {"type": "error", "message": "Local Ollama fallback is disabled."}
            return
        selected_model = _normalize_model_choice(model) or self.config.model
        payload = {
            "model": selected_model,
            "stream": True,
            "think": think,
            "messages": self._compose_messages(prompt, system_prompt=system_prompt, messages=messages),
            "options": {"temperature": self.config.temperature},
        }
        if options:
            payload["options"].update(options)
        if response_format is not None:
            payload["format"] = response_format
        payload = self._stabilize_payload(payload)
        request = Request(
            self.config.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with self._locked_urlopen(request, timeout=timeout_seconds or self.config.timeout_seconds) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    message = data.get("message", {}) or {}
                    content = str(message.get("content") or "")
                    thinking = str(message.get("thinking") or "")
                    if thinking:
                        yield {"type": "thinking_delta", "delta": thinking}
                    if content:
                        yield {"type": "content_delta", "delta": content}
                    if data.get("done"):
                        yield {"type": "ollama_done", "data": data}
                        return
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if think and exc.code == 400 and "does not support thinking" in body.lower():
                yield from self.stream_events(
                    prompt,
                    system_prompt=system_prompt,
                    response_format=response_format,
                    model=model,
                    options=options,
                    think=False,
                    timeout_seconds=timeout_seconds,
                    messages=messages,
                )
                return
            yield {"type": "error", "message": f"Ollama HTTP {exc.code}: {body}"}
        except URLError as exc:
            yield {"type": "error", "message": f"Failed to reach Ollama: {exc}"}
        except TimeoutError as exc:
            yield {"type": "error", "message": f"Timed out waiting for Ollama: {exc}"}
        except OSError as exc:
            yield {"type": "error", "message": f"Ollama request failed: {exc}"}

    def _stream_request(self, request: Request, *, timeout_seconds: int | None = None) -> ActionResult:
        try:
            with self._locked_urlopen(request, timeout=timeout_seconds or self.config.timeout_seconds) as response:
                chunks: list[str] = []
                while True:
                    chunk = response.read(4096)
                    if not chunk:
                        break
                    text = chunk.decode("utf-8")
                    for line in text.strip().split("\\n"):
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

    def _compose_messages(
        self,
        prompt: str,
        *,
        system_prompt: str | None,
        messages: list[dict[str, str]] | None,
    ) -> list[dict[str, str]]:
        combined_system = self._compose_system_prompt(system_prompt)
        chat_messages: list[dict[str, str]] = [{"role": "system", "content": combined_system}]
        for item in messages or []:
            role = str(item.get("role") or "").strip().lower()
            content = str(item.get("content") or "").strip()
            if not content or role not in {"system", "user", "assistant"}:
                continue
            if role == "system":
                chat_messages[0]["content"] = f"{chat_messages[0]['content']}\n\n{content}".strip()
            else:
                chat_messages.append({"role": role, "content": content})

        prompt_text = str(prompt or "").strip()
        if prompt_text and (len(chat_messages) == 1 or chat_messages[-1].get("role") != "user" or chat_messages[-1].get("content", "").strip() != prompt_text):
            chat_messages.append({"role": "user", "content": prompt_text})
        return chat_messages

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
