# Dialog

A local-first spoken dialog loop that captures microphone audio, transcribes it with
[Faster-Whisper](https://github.com/SYSTRAN/faster-whisper), and speaks responses using an
offline text-to-speech engine. The project is packaged as a CLI that can run an interactive
loop or a lighter dictation daemon.

## Getting Started

The project uses [uv](https://github.com/astral-sh/uv) for dependency management, but you can
also install it with `pip`. Earlier revisions specified `numpy>=2.3.4`, a version that does
not exist on PyPI, which caused `uv` resolution failures. The dependency has been relaxed to a
valid range so that `uv pip install` works again.

```bash
uv pip install -e .
# or
pip install -e .
```

Optional runtime dependencies:

- `sounddevice` for microphone capture.
- `faster-whisper` for speech-to-text (downloads models on first use).
- `pyttsx3` for local text-to-speech.

The code now imports these lazily and will raise friendly runtime errors if a capability is
invoked without the matching extra installed.

## Running

```bash
uv run dialog
```

Type into the prompt or speak into the microphone. Use `exit`/`quit` or `Ctrl+C` to stop.

For transcription-only background dictation:

```bash
python -m dialog.dictation_daemon
```

## Development

- Read the high-level architecture and task planning in
  [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- Run the test suite with `pytest`:

  ```bash
  uv run pytest
  ```

The core classes support dependency injection, making it possible to unit-test the transcription
logic and dialog response loop without audio hardware.

## License

MIT
