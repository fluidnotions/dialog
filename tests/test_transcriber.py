import queue
import time

from dialog.transcriber import Transcriber


class DummySegment:
    def __init__(self, text: str) -> None:
        self.text = text


class DummyModel:
    def __init__(self) -> None:
        self.calls: list[list[float]] = []

    def transcribe(self, buffer, beam_size: int = 1):
        if hasattr(buffer, "tolist"):
            buffer = buffer.tolist()
        self.calls.append(list(buffer))
        return [DummySegment("hello world")], None


def test_process_chunk_emits_text_once_threshold_reached():
    audio_queue: queue.Queue[list[float]] = queue.Queue()
    captured: list[str] = []
    model = DummyModel()
    transcriber = Transcriber(
        audio_queue,
        sample_rate=4,
        segment_duration=0.5,
        model=model,
        on_text=captured.append,
    )

    transcriber.process_chunk([1.0])
    assert captured == []

    transcriber.process_chunk([1.0])
    assert captured == ["hello world"]
    assert model.calls  # ensure the model was invoked


def test_thread_worker_drains_queue_and_stops_cleanly():
    audio_queue: queue.Queue[list[float]] = queue.Queue()
    captured: list[str] = []
    model = DummyModel()
    transcriber = Transcriber(
        audio_queue,
        sample_rate=4,
        segment_duration=0.5,
        model=model,
        on_text=captured.append,
    )

    transcriber.start()
    audio_queue.put([1.0, 1.0])

    timeout = time.time() + 2
    while not captured and time.time() < timeout:
        time.sleep(0.05)

    transcriber.stop()

    assert captured == ["hello world"]
    assert not transcriber.thread or not transcriber.thread.is_alive()
