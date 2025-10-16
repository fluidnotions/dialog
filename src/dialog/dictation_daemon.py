import time
from audio_capture import AudioCapture
from transcriber import Transcriber


class DictationDaemon:
    """Coordinates capture and transcription threads."""

    def __init__(self, use_gpu: bool = False):
        self.capture = AudioCapture()
        self.transcriber = Transcriber(self.capture.queue, use_gpu=use_gpu)

    def start(self) -> None:
        print("[Daemon] starting capture + transcription…")
        self.capture.start()
        self.transcriber.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        print("[Daemon] stopping…")
        self.capture.stop()
        self.transcriber.stop()
