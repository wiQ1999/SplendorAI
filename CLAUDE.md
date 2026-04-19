# CLAUDE.md — Splendor AI

Python implementation of the Splendor board game with an AlphaZero-style AI opponent. The game engine is trained via self-play (OpenSpiel + PyTorch) and deployed as an ONNX model consumed by two end-user apps: a terminal app and a desktop GUI — neither depends on the training stack.

For general project info see README.md.

## Codebase map

Monorepo managed with `uv` workspaces. Each directory under `packages/` is an independent Python package. Dependency flow is strictly one-directional:

```
splendor-core → splendor-openspiel → splendor-training
splendor-core → splendor-inference → splendor-cli/splendor-gui
```

| Package | Purpose |
|---|---|
| `splendor-core` | Game rules engine — single source of truth, minimal dependencies |
| `splendor-openspiel` | OpenSpiel adapter for training, no game logic |
| `splendor-training` | Self-play loop, exports trained model to ONNX |
| `splendor-inference` | ONNX runtime wrapper, no OpenSpiel or PyTorch |
| `splendor-cli` | Terminal application (`rich`, `textual`) |
| `splendor-gui` | Desktop GUI application (PySide6 / Qt 6) |

## Essential commands

```bash
uv sync                                    # install / sync environment
uv run pytest                              # full test suite
uv run ruff check .                        # check files
uv run ruff format .                       # format files
uv run pyright .\packages\<directory>      # type checking
uv add --package <package-name> <dep>      # add a dependency
uv run splendor                            # launch CLI
uv run python -m splendor_gui              # launch GUI
```

## Key constraints

- `splendor-cli` and `splendor-gui` must never import from `splendor-openspiel` or `splendor-training`.
- Never use `Any` in type annotations — pyright runs in strict mode.
- Never use `print()` outside `splendor-cli` and `splendor-gui`.
- Never commit `.onnx` files directly — use Git LFS.
- Always add dependencies per-package: `uv add --package <n> <dep>`.

## Reference docs

Read these before working on the relevant area:

| File | When to read |
|---|---|
| `docs/game-rules.md` | Implementing or modifying any game logic |
| `docs/architecture.md` | Changing package boundaries or dependencies |