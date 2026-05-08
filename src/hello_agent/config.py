from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import tomllib


@dataclass
class ToolConfig:
    backend: str = "ollama"
    model: str = "gemma4:e2b"
    base_url: str = "http://localhost:11434"
    auto_pull: bool = True


@dataclass
class Config:
    tool: ToolConfig = field(default_factory=ToolConfig)

    @classmethod
    def discover(cls) -> Config:
        """Look for config in project root and user config dirs."""
        config_path = cls._search_config_path()
        if config_path and config_path.exists():
            with open(config_path, "rb") as fh:
                raw = tomllib.load(fh)
            tool_data = raw.get("tool", {}).get("hello_agent", {})
            return cls(
                tool=ToolConfig(
                    backend=tool_data.get("backend", "ollama"),
                    model=tool_data.get("model", "gemma4:e2b"),
                    base_url=tool_data.get("base_url", "http://localhost:11434"),
                    auto_pull=tool_data.get("auto_pull", True),
                )
            )
        return cls()

    @staticmethod
    def _search_config_path() -> Optional[Path]:
        candidates = [
            Path.cwd() / "hello-agent.toml",
            Path(__file__).parent.parent.parent.parent / "hello-agent.toml",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None