from __future__ import annotations

import queue
import threading
from collections.abc import Callable, Iterator
from typing import Any, ContextManager, Optional

try:
    import sounddevice as sd
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    sd = None  # type: ignore[assignment]


StreamFactory = Callable[[], ContextManager["_InputStream"]]


class _InputStream(Iterator[Any]):
    def read(self, samples: int) -> tuple[Any, Optional[object]]: ...

    def __enter__(self) -> "_InputStream": ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...


class AudioCapture:
    """Captures microphone audio in small chunks and pushes them to a queue."""

    def __init__(
        self,
        sample_rate: int = 16_000,
        chunk_duration: float = 1.0,
        stream_factory: StreamFactory | None = None,
    ):
        self.sample_rate = sample_rate
        self.chunk_samples = int(sample_rate * chunk_duration)
        self.queue: queue.Queue[Any] = queue.Queue(maxsize=10)
        self.stop_event = threading.Event()
        self._stream_factory = stream_factory or self._default_stream_factory
        self.thread: threading.Thread | None = None
        self.last_error: Exception | None = None

    def _stream_loop(self) -> None:
        try:
            with self._stream_factory() as stream:
                while not self.stop_event.is_set():
                    data, _ = stream.read(self.chunk_samples)
                    self._enqueue_chunk(data)
        except Exception as e:
            self.last_error = e
            print(f"[AudioCapture] error: {e}")

    def _enqueue_chunk(self, data: Any) -> None:
        size = getattr(data, "size", None)
        if size == 0:
            return
        copy: Any
        if hasattr(data, "copy"):
            copy = data.copy()
        else:
            copy = list(data)
            if not copy:
                return
        try:
            self.queue.put_nowait(copy)
        except queue.Full:
            self.queue.get_nowait()  # drop oldest
            self.queue.put_nowait(copy)

    def _default_stream_factory(self) -> ContextManager["_InputStream"]:
        if sd is None:
            raise RuntimeError(
                "sounddevice is not installed. Install the 'sounddevice' extra to enable audio capture."
            )
        return sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.chunk_samples,
        )

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=1)
