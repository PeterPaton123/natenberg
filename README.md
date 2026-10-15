# Natenberg

Python notebooks for learning options pricing, with NumPy, SciPy, pandas,
Matplotlib, and JupyterLab. Requires Python 3.12 or newer.

## Setup

Install uv if needed (macOS/Linux):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

From this directory, install the packages and Ruff into `.venv`:

```sh
uv sync
uv run jupyter lab
```

In VS Code, select `.venv/bin/python` as the notebook kernel.

## Add packages

```sh
uv add sympy           # Add a notebook dependency
uv add --dev pytest   # Add a development dependency
```

## Lint and format

Ruff uses [Black-compatible formatting](https://docs.astral.sh/ruff/formatter/)
with 88-character lines, double quotes, and spaces. These commands cover Python
files and notebooks:

```sh
uv run ruff check --fix .
uv run ruff format .
```

Commit `uv.lock` to keep package versions reproducible.
