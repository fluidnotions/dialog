from faster_whisper import WhisperModel
import numpy as np
import queue
import threading


class Transcriber:
    """Consumes audio chunks and performs transcription using Faster-Whisper."""

    def __init__(self, audio_queue: queue.Queue, model_size: str = "base", use_gpu: bool = False):
        self.audio_queue = audio_queue
        self.model_size = model_size
        self.use_gpu = use_gpu
        self.stop_event = threading.Event()
        device = "cuda" if use_gpu else "cpu"
        self.model = WhisperModel(model_size, device=device)
        self.buffer = np.zeros((0,), dtype=np.float32)

    def _worker(self) -> None:
        print("[Transcriber] ready.")
        while not self.stop_event.is_set():
            try:
                chunk = self.audio_queue.get(timeout=1)
                self.buffer = np.concatenate((self.buffer, chunk.flatten()))
                if len(self.buffer) >= self.model.feature_extractor.sampling_rate * 5:
                    segments, _ = self.model.transcribe(self.buffer, beam_size=1)
                    text = "".join(seg.text for seg in segments).strip()
                    if text:
                        print(f"[Transcriber] {text}")
                    self.buffer = np.zeros((0,), dtype=np.float32)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[Transcriber] error: {e}")

    def start(self) -> None:
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=1)
