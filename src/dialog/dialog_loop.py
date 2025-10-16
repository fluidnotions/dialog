import queue
import threading
import time
from transcriber import Transcriber
from audio_capture import AudioCapture
from tts_engine import TextToSpeech


class DialogLoop:
    """Runs a full duplex audio dialog: listen → transcribe → reply (TTS)."""

    def __init__(self, use_gpu: bool = False):
        self.capture = AudioCapture()
        self.transcriber = Transcriber(self.capture.queue, use_gpu=use_gpu)
        self.tts = TextToSpeech()
        self.responses: queue.Queue[str] = queue.Queue()
        self.stop_event = threading.Event()

    def start(self) -> None:
        """Launch capture + transcription threads and TTS responder."""
        self.capture.start()
        self.transcriber.start()
        threading.Thread(target=self._response_loop, daemon=True).start()
        print("[Dialog] ready. Type messages or speak into mic.")
        try:
            while not self.stop_event.is_set():
                user_input = input("> ").strip()
                if user_input.lower() in {"exit", "quit"}:
                    self.stop()
                    break
                if user_input:
                    self.responses.put(user_input)
        except KeyboardInterrupt:
            self.stop()

    def _response_loop(self) -> None:
        """Consumes queued responses and speaks them."""
        while not self.stop_event.is_set():
            try:
                text = self.responses.get(timeout=0.5)
                print(f"[Dialog] speaking: {text}")
                self.tts.speak_async(text)
            except queue.Empty:
                continue

    def stop(self) -> None:
        print("[Dialog] stopping…")
        self.stop_event.set()
        self.capture.stop()
        self.transcriber.stop()
