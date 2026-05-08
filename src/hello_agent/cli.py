from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.request

from hello_agent import __version__
from hello_agent.config import Config
from hello_agent.ollama_setup import (
    OllamaConfig,
    ensure_model_ready,
    list_models,
    model_is_available,
    ollama_is_running,
    pull_model,
    require_ollama_installed,
)


def cmd_doctor(config: Config) -> int:
    """Check environment: Ollama binary, server, and model availability."""
    print("=== hello-agent doctor ===\n")

    # Check Ollama binary
    print("[1/3] Checking ollama binary...")
    if shutil.which("ollama") is None:
        print("  FAIL  ollama not found on PATH")
        print("  Install from https://ollama.com\n")
        return 1
    print("  OK    ollama is on PATH")

    # Check server
    print("[2/3] Checking Ollama server...")
    if not ollama_is_running(config.tool.base_url):
        print(f"  FAIL  server not reachable at {config.tool.base_url}")
        print("  Start it with:  ollama serve\n")
        return 1
    print("  OK    server is running")

    # Check model
    print("[3/3] Checking model...")
    model = config.tool.model
    if model_is_available(config.tool.base_url, model):
        print(f"  OK    model {model!r} is available")
    else:
        print(f"  FAIL  model {model!r} is not installed")
        print(f"  Run 'hello-agent setup' to download it.\n")
        return 1

    print("\nAll checks passed.")
    return 0


def cmd_setup(config: Config, background: bool = False) -> int:
    """Download the model (optionally in background)."""
    require_ollama_installed()

    if not ollama_is_running(config.tool.base_url):
        print("Ollama server is not running. Start it with:  ollama serve")
        return 1

    model = config.tool.model
    if model_is_available(config.tool.base_url, model):
        print(f"Model {model!r} is already installed.")
        return 0

    if background:
        subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"Background download started: ollama pull {model}")
        print("Check progress with:  ollama list")
        return 0

    pull_model(model)
    return 0


def cmd_ask(config: Config, prompt: str) -> int:
    """Send a prompt to the model, ensuring it is ready first."""
    ollama_config = OllamaConfig(
        model=config.tool.model,
        base_url=config.tool.base_url,
        auto_pull=config.tool.auto_pull,
    )
    ensure_model_ready(ollama_config)

    result = subprocess.run(
        ["ollama", "run", config.tool.model, prompt],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return 1
    print(result.stdout, end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hello-agent",
        description="Local AI CLI powered by Ollama",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    # doctor
    sub.add_parser("doctor", help="Check environment and model availability")

    # setup
    setup_parser = sub.add_parser("setup", help="Download the model")
    setup_parser.add_argument(
        "--background", action="store_true",
        help="Run the download in the background",
    )

    # ask
    ask_parser = sub.add_parser("ask", help="Send a prompt to the model")
    ask_parser.add_argument(
        "prompt", nargs="+",
        help="Prompt text (joins all args with spaces)",
    )

    args = parser.parse_args(argv)
    config = Config.discover()

    if args.command == "doctor":
        return cmd_doctor(config)
    elif args.command == "setup":
        return cmd_setup(config, background=args.background)
    elif args.command == "ask":
        prompt = " ".join(args.prompt)
        return cmd_ask(config, prompt)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())