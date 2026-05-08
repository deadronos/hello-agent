# hello-agent

Local AI CLI powered by Ollama.

## Requirements

- [Ollama](https://ollama.com) installed and running (`ollama serve`)
- Python 3.11+

## Quick start

```bash
pip install -e .
```

## Default model

```text
gemma4:e2b
```

## Commands

### `hello-agent doctor`

Check environment: Ollama binary, server, and model availability.

### `hello-agent setup`

Download the model. Runs interactively in the foreground by default.

```bash
hello-agent setup           # visible blocking download
hello-agent setup --background  # background download
```

### `hello-agent ask`

Send a prompt to the model. On first use, the model is downloaded automatically if `auto_pull = true`.

```bash
hello-agent ask "Say hello from a local model."
```

## Configuration

Create `hello-agent.toml` in the project root:

```toml
[tool.hello_agent]
backend = "ollama"
model   = "gemma4:e2b"
base_url = "http://localhost:11434"
auto_pull = true
```

Or use environment variables / defaults — no config file is required to get started.

## First-run behaviour

On first use, `hello-agent` checks whether the configured local model exists.

If Ollama is installed and running, the CLI can download the model automatically:

```bash
hello-agent ask "Say hello from a local model."
```

To prepare everything explicitly:

```bash
hello-agent doctor
hello-agent setup
```