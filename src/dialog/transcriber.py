from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from typing import Any

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    np = None  # type: ignore[assignment]

try:
    from faster_whisper import WhisperModel
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    WhisperModel = None  # type: ignore[misc, assignment]


class Transcriber:
    """Consumes audio chunks and performs transcription using Faster-Whisper."""

    def __init__(
        self,
        audio_queue: "queue.Queue[Any]",
        model_size: str = "base",
        use_gpu: bool = False,
        sample_rate: int = 16_000,
        segment_duration: float = 5.0,
        model: Any | None = None,
        on_text: Callable[[str], None] | None = None,
    ):
        self.audio_queue = audio_queue
        self.model_size = model_size
        self.use_gpu = use_gpu
        self.sample_rate = sample_rate
        self.segment_duration = segment_duration
        self.stop_event = threading.Event()
        self.model = model or self._create_model()
        self.buffer: list[float] = []
        self.thread: threading.Thread | None = None
        self.last_error: Exception | None = None
        self.on_text = on_text or self._default_on_text

    def _worker(self) -> None:
        print("[Transcriber] ready.")
        while not self.stop_event.is_set():
            try:
                chunk = self.audio_queue.get(timeout=1)
                self.process_chunk(chunk)
            except queue.Empty:
                continue
            except Exception as e:
                self.last_error = e
                print(f"[Transcriber] error: {e}")

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=1)

    def process_chunk(self, chunk: Any) -> None:
        self.buffer.extend(self._flatten(chunk))
        threshold = int(self.sample_rate * self.segment_duration)
        if len(self.buffer) < threshold:
            return
        segments, _ = self.model.transcribe(self._model_input(), beam_size=1)
        text = "".join(getattr(seg, "text", "") for seg in segments).strip()
        if text:
            self.on_text(text)
        self.buffer = []

    def _create_model(self) -> Any:
        if WhisperModel is None:
            raise RuntimeError(
                "faster-whisper is not installed. Install the 'faster-whisper' extra to enable transcription."
            )
        device = "cuda" if self.use_gpu else "cpu"
        return WhisperModel(self.model_size, device=device)

    @staticmethod
    def _default_on_text(text: str) -> None:
        print(f"[Transcriber] {text}")

    def _flatten(self, chunk: Any) -> list[float]:
        if np is not None:
            return np.asarray(chunk, dtype=np.float32).reshape(-1).tolist()
        if isinstance(chunk, list):
            flat: list[float] = []
            for item in chunk:
                if isinstance(item, list):
                    flat.extend(float(x) for x in item)
                else:
                    flat.append(float(item))
            return flat
        if isinstance(chunk, tuple):
            return [float(x) for x in chunk]
        try:
            return [float(chunk)]
        except TypeError:
            raise TypeError("Unsupported audio chunk type") from None

    def _model_input(self) -> Any:
        if np is not None:
            return np.asarray(self.buffer, dtype=np.float32)
        return list(self.buffer)
