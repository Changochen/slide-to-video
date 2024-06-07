from .base_engine import TTSEngine
from .registery import register_engine


class LocalTTSEngine(TTSEngine):
    def __init__(self, config: dict):
        super().__init__(**config)
        must_have_keys = ["voice"]
        for key in must_have_keys:
            if key not in config:
                raise ValueError(f"Missing required key: {key}")
        self.tts = None
        self.voice_sample_path = config["voice"]

    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        print(f"Generating audio file for text: {text} at speed {self.speed}")
        self.get_tts().tts_to_file(
            text=text.strip(),
            speaker_wav=self.voice_sample_path,
            language="en",
            file_path=output_path,
        )
        print(f"Audio file generated and saved as {output_path}")

    def parallizable(self):
        return False

    def get_tts(self):
        if self.tts:
            return self.tts
        import torch
        from TTS.api import TTS

        # Get device
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # List available 🐸TTS models
        # print(TTS().list_models())

        # Init TTS
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        self.tts = tts
        return tts


register_engine("local", LocalTTSEngine)
