# Splendor AI

A Python implementation of the [Splendor](https://www.spacecowboys.fr/splendor) board game with an AI opponent trained via self-play using an AlphaZero-style neural network.

Play against the AI in the terminal or in a graphical desktop application.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

```bash
git clone https://github.com/wiQ1999/SplendorAI.git
cd SplendorAI
uv sync
```

## Usage

**Terminal application:**

```bash
uv run splendor
```

**Desktop GUI:**

```bash
uv run python -m splendor_gui
```

## How it works

The AI is trained through self-play using [OpenSpiel](https://github.com/google-deepmind/open_spiel) and PyTorch. The trained model is exported to ONNX and loaded by both applications at runtime — neither app depends on the training stack.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. Make sure all tests pass before submitting:

```bash
uv run pytest
uv run pyright .\packages\<DIRECTORY>
```

## License

[MIT](LICENSE)