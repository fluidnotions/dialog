# Dialog Application Architecture

## Project Purpose
The project is intended to provide a local-first spoken dialog loop: capture audio from a
microphone, transcribe it to text with Faster-Whisper, and respond using an offline
text-to-speech (TTS) engine. The CLI entry point launches a duplex loop that also accepts
text typed by the user and speaks it aloud.

## Current Components
- `dialog.audio_capture.AudioCapture` – wraps `sounddevice.InputStream` and enqueues raw
  audio chunks.
- `dialog.transcriber.Transcriber` – consumes audio chunks, stitches them into a buffer and
  transcribes them with a Faster-Whisper model.
- `dialog.tts_engine.TextToSpeech` – wraps `pyttsx3` for local speech synthesis.
- `dialog.dialog_loop.DialogLoop` – orchestrates capture, transcription, and spoken
  responses, allowing typed input.
- `dialog.dictation_daemon.DictationDaemon` – lighter wrapper that only captures and
  transcribes, useful for background dictation.
- `dialog.main` – console entry point that instantiates the dialog loop.

## Observed Issues
1. **Dependency resolution fails** – the pinned requirement `numpy>=2.3.4` references a
   version that does not exist on PyPI, causing `uv` (and `pip`) installs to fail. Several
   dependencies are heavyweight and optional, but currently imported eagerly, making the
   package unusable without audio hardware libraries installed.
2. **Import topology** – modules use absolute imports that only work when executed from the
   project root and not when installed as a package.
3. **Testability** – core classes spin up threads immediately and directly talk to external
   libraries, making them hard to unit test or run in environments without audio support.
4. **Lifecycle management** – there is no graceful shutdown for the dialog loop besides
   hitting `KeyboardInterrupt`, and there is little resilience to runtime errors.

## Improvement Plan
- Loosen and document the dependency versions so `uv` can resolve them. Defer optional
  imports until runtime and surface clear errors when a capability is missing.
- Refactor classes to allow dependency injection and introduce small test-friendly helper
  methods, enabling unit tests to run without audio/ML libraries.
- Correct package-relative imports and tidy the public API.
- Add documentation describing setup, architecture, and operational notes.
- Introduce automated tests covering the transcription flow and dialog response queue to
  guard future refactors.

## Task Breakdown & Agent Assignment
1. **Environment Bring-up (Build Agent)**
   - Fix dependency metadata and document installation steps.
   - Ensure optional dependencies are imported lazily with actionable error messages.
2. **Core Refactor (Core Agent)**
   - Introduce dependency injection hooks for audio capture, transcription, and TTS.
   - Expose testable helper methods without requiring threads or hardware.
3. **Testing (QA Agent)**
   - Add pytest-based unit tests for the transcription buffer logic and dialog response
     handling.
   - Validate thread lifecycle helpers via deterministic unit tests.
4. **Documentation (Docs Agent)**
   - Update the README with usage instructions, dependency notes, and development workflow.
   - Capture the architectural overview and TODO list (this document).

Each agent can work independently now that the required hooks and documentation tasks have
been enumerated. Coordination happens via the shared TODO list below.

## TODO Checklist
- [x] Update dependency versions and explain UV installation quirks.
- [x] Refactor imports and optional dependency handling.
- [x] Add deterministic helper methods for processing audio chunks.
- [x] Write pytest coverage for transcription logic and dialog response queue.
- [x] Document usage, testing, and architecture in README.

