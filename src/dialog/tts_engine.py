import pyttsx3
import threading


class TextToSpeech:
    """Simple local text-to-speech engine using pyttsx3 (offline)."""

    def __init__(self, voice: str | None = None, rate: int = 180):
        self.engine = pyttsx3.init()
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
