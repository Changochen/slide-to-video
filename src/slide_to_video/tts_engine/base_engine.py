from abc import ABC, abstractmethod
from typing import List
import concurrent.futures


class TTSEngine(ABC):
    def __init__(self, *, speech_speed=1.0, **kwargs):
        self.speed = speech_speed

    @abstractmethod
    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        pass

    @abstractmethod
    def parallizable(self) -> bool:
        pass

    def par_synthesize(
        self,
        texts: List[str],
        output_paths: List[str],
        *,
        format: str = "wav",
    ):
        if self.parallizable():
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for text, output_path in zip(texts, output_paths):
                    future = executor.submit(self.synthesize, text, output_path)
                    futures.append(future)

                    concurrent.futures.wait(futures)
        else:
            for text, output_path in zip(texts, output_paths):
                self.synthesize(text, output_path)
