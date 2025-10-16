import sounddevice as sd
import numpy as np
import queue
import threading


class AudioCapture:
    """Captures microphone audio in small chunks and pushes them to a queue."""

    def __init__(self, sample_rate: int = 16_000, chunk_duration: float = 1.0):
        self.sample_rate = sample_rate
        self.chunk_samples = int(sample_rate * chunk_duration)
        self.queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=10)
        self.stop_event = threading.Event()

    def _stream_loop(self) -> None:
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=self.chunk_samples,
            ) as stream:
                while not self.stop_event.is_set():
                    data, _ = stream.read(self.chunk_samples)
                    try:
                        self.queue.put_nowait(data.copy())
                    except queue.Full:
                        self.queue.get_nowait()  # drop oldest
                        self.queue.put_nowait(data.copy())
        except Exception as e:
            print(f"[AudioCapture] error: {e}")

    def start(self) -> None:
        self.thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=1)
