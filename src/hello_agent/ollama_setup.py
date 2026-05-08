from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.request
from dataclasses import dataclass


@dataclass
class OllamaConfig:
    model: str = "gemma4:e2b"
    base_url: str = "http://localhost:11434"
    auto_pull: bool = True


def require_ollama_installed() -> None:
    if shutil.which("ollama") is None:
        raise RuntimeError(
            "Ollama is not installed or not on PATH.\n"
            "Install it from https://ollama.com, then run:\n"
            "  ollama serve\n"
        )


def ollama_is_running(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def list_models(base_url: str) -> set[str]:
    with urllib.request.urlopen(f"{base_url}/api/tags", timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))

    names: set[str] = set()
    for model in payload.get("models", []):
        name = model.get("name")
        if name:
            names.add(name)
            names.add(name.split(":")[0])
    return names


def model_is_available(base_url: str, model: str) -> bool:
    models = list_models(base_url)
    return model in models


def pull_model(model: str) -> None:
    print(f"Downloading local model: {model}")
    print("This can take a while on first run.\n")

    process = subprocess.Popen(
        ["ollama", "pull", model],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    assert process.stdout is not None

    total_str = ""
    bar = None

    for raw in process.stdout:
        line = raw.rstrip()

        # Parse progress lines from ollama pull output:
        #   pulling a3d...  12% ████░░░░░░  1.2GB/10GB  5.6GB/s
        if "%" in line and ("█" in line or "/" in line):
            parts = line.split()
            for i, tok in enumerate(parts):
                if tok.startswith("#"):
                    continue
                if "%" in tok:
                    pct_str = tok.replace("%", "")
                    try:
                        pct = float(pct_str)
                        if bar is None:
                            # Simple inline progress bar
                            bar = _ProgressBar()
                        bar.update(pct)
                    except ValueError:
                        pass
                    break
            print(f"\r  {line}  ", end="", flush=True)
        else:
            if bar is not None:
                bar.finish()
                bar = None
                print()
            print(f"  {line}")

    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError(f"ollama pull {model} failed with exit code {exit_code}")


class _ProgressBar:
    """Lightweight inline progress bar — no dependencies."""

    _WIDTH = 30

    def __init__(self) -> None:
        self._pct = 0.0

    def update(self, pct: float) -> None:
        self._pct = pct
        filled = int(round(self._WIDTH * pct / 100))
        bar_str = "█" * filled + "░" * (self._WIDTH - filled)
        print(f"\r  [{bar_str}] {pct:5.1f}%", end="", flush=True)

    def finish(self) -> None:
        self.update(100.0)
        print(flush=True)


def ensure_model_ready(config: OllamaConfig) -> None:
    require_ollama_installed()

    if not ollama_is_running(config.base_url):
        raise RuntimeError(
            "Ollama is installed, but the Ollama server is not running.\n"
            "Start it with:\n"
            "  ollama serve\n"
        )

    if model_is_available(config.base_url, config.model):
        return

    if not config.auto_pull:
        raise RuntimeError(
            f"Model {config.model!r} is not installed.\n"
            f"Run:\n"
            f"  ollama pull {config.model}\n"
        )

    pull_model(config.model)