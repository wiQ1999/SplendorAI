# Architecture

## Package dependency graph

```
splendor-core
    ├── splendor-openspiel  (training only)
    │       └── splendor-training
    └── splendor-inference  (runtime only)
            ├── splendor-cli
            └── splendor-gui
```

The graph is strictly acyclic. `splendor-core` has no dependencies on any other workspace package. `splendor-cli` and `splendor-gui` must never depend on `splendor-openspiel` or `splendor-training`.

## Training / runtime boundary

The only artefact crossing the boundary between the training stack and the runtime applications is the exported ONNX model (`models/policy.onnx`).

```
[splendor-training] -- export --> models/policy.onnx -- load --> [splendor-inference]
```

This ensures that end-user applications carry no dependency on OpenSpiel or PyTorch.

## Package responsibilities

| Package | Key dependencies | Role |
|---|---|---|
| `splendor-core` | — | Game rules, state, legal actions |
| `splendor-openspiel` | `open_spiel` | OpenSpiel adapter for self-play |
| `splendor-training` | `torch`, `splendor-openspiel` | Self-play loop, ONNX export |
| `splendor-inference` | `onnxruntime` | Policy/value prediction at runtime |
| `splendor-cli` | `rich`, `textual` | Terminal application |
| `splendor-gui` | `PySide6` | Desktop GUI application |

## Workspace management

Monorepo managed with `uv` workspaces. Each package under `packages/` has its own `pyproject.toml`. All packages share a single virtual environment rooted at the repository level.

Cross-package dependencies are declared as standard `dependencies` entries and resolved locally via `[tool.uv.sources]` in the root `pyproject.toml` — no publishing to PyPI required.
