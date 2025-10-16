import queue
import threading

from dialog.dialog_loop import DialogLoop


class DummyCapture:
    def __init__(self) -> None:
        self.queue: queue.Queue[str] = queue.Queue()
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


class DummyTranscriber:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


class DummyTTS:
    def __init__(self) -> None:
        self.spoken: list[str] = []
        self._event = threading.Event()

    def speak_async(self, text: str) -> None:
        self.spoken.append(text)
        self._event.set()

    def wait_for_speech(self, timeout: float) -> bool:
        return self._event.wait(timeout)


def test_response_loop_speaks_enqueued_text():
    capture = DummyCapture()
    transcriber = DummyTranscriber()
    tts = DummyTTS()
    loop = DialogLoop(capture=capture, transcriber=transcriber, tts=tts)

    loop.start(with_cli=False)
    loop.enqueue_response("testing")

    assert tts.wait_for_speech(1.0)
    assert tts.spoken == ["testing"]

    loop.stop()

    assert capture.started and capture.stopped
    assert transcriber.started and transcriber.stopped
