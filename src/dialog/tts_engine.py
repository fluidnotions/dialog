from __future__ import annotations

import threading
from typing import Any

try:
    import pyttsx3
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    pyttsx3 = None  # type: ignore[assignment]


class TextToSpeech:
    """Simple local text-to-speech engine using pyttsx3 (offline)."""

    def __init__(self, voice: str | None = None, rate: int = 180, engine: Any | None = None):
        self.engine = engine or self._create_engine()
        if voice:
            for v in self.engine.getProperty("voices"):
                if voice.lower() in v.name.lower():
                    self.engine.setProperty("voice", v.id)
                    break
        self.engine.setProperty("rate", rate)
        self.lock = threading.Lock()

    def speak(self, text: str) -> None:
        """Speak text synchronously (thread-safe)."""
        with self.lock:
            self.engine.say(text)
            self.engine.runAndWait()

    def speak_async(self, text: str) -> None:
        """Fire-and-forget version."""
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()

    @staticmethod
    def _create_engine() -> Any:
        if pyttsx3 is None:
            raise RuntimeError(
                "pyttsx3 is not installed. Install the 'pyttsx3' extra to enable text-to-speech."
            )
        return pyttsx3.init()
