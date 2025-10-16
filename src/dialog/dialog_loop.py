from __future__ import annotations

import queue
import threading
from collections.abc import Callable

from .audio_capture import AudioCapture
from .transcriber import Transcriber
from .tts_engine import TextToSpeech


class DialogLoop:
    """Runs a full duplex audio dialog: listen → transcribe → reply (TTS)."""

    def __init__(
        self,
        use_gpu: bool = False,
        capture: AudioCapture | None = None,
        transcriber: Transcriber | None = None,
        tts: TextToSpeech | None = None,
    ):
        self.capture = capture or AudioCapture()
        self.transcriber = transcriber or Transcriber(self.capture.queue, use_gpu=use_gpu)
        self.tts = tts or TextToSpeech()
        self.responses: queue.Queue[str] = queue.Queue()
        self.stop_event = threading.Event()
        self._response_thread: threading.Thread | None = None

    def start(self, with_cli: bool = True, input_fn: Callable[[str], str] = input) -> None:
        """Launch capture + transcription threads and TTS responder."""
        if self._response_thread and self._response_thread.is_alive():
            return
        self.stop_event.clear()
        self.capture.start()
        self.transcriber.start()
        self._response_thread = threading.Thread(target=self._response_loop, daemon=True)
        self._response_thread.start()
        print("[Dialog] ready. Type messages or speak into mic.")
        if with_cli:
            try:
                self._cli_loop(input_fn)
            except KeyboardInterrupt:
                self.stop()

    def _cli_loop(self, input_fn: Callable[[str], str]) -> None:
        while not self.stop_event.is_set():
            user_input = input_fn("> ").strip()
            if user_input.lower() in {"exit", "quit"}:
                self.stop()
                break
            if user_input:
                self.responses.put(user_input)

    def _response_loop(self) -> None:
        """Consumes queued responses and speaks them."""
        while not self.stop_event.is_set():
            try:
                text = self.responses.get(timeout=0.5)
                print(f"[Dialog] speaking: {text}")
                self.tts.speak_async(text)
            except queue.Empty:
                continue

    def enqueue_response(self, text: str) -> None:
        if text:
            self.responses.put(text)

    def stop(self) -> None:
        print("[Dialog] stopping…")
        self.stop_event.set()
        self.capture.stop()
        self.transcriber.stop()
        if self._response_thread:
            self._response_thread.join(timeout=1)
