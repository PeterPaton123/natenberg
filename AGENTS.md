# Project purpose

Learn options pricing through Python notebooks that connect financial theory with numerical examples.

## Coding guidelines

- Use `uv` to manage dependencies and run Python commands; add packages with `uv add`.
- Use Ruff for linting and Black-compatible formatting: `uv run ruff check --fix .` and `uv run ruff format .`.

## Markdown guidelines

- Do not use em-dashes.

## Preserving manual edits

- Re-read each file from disk immediately before editing it, especially notebooks. Never edit from a previously cached copy or assume the file is unchanged since the last turn.
- Make only the targeted changes needed for the current request. Preserve the user's manual edits to notebook cells, prose, code, and formatting outside that scope.
- Before executing a notebook in place, re-read its latest contents. Wait for execution to finish before making another edit, since execution can overwrite the notebook file.
- If the file changes while preparing an edit, re-read it and apply the intended change to the latest version rather than overwriting it with an older version.
