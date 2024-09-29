import concurrent.futures
from typing import List
import hashlib
import os
from pydub import AudioSegment
from moviepy.editor import VideoFileClip


def par_execute(func, *args) -> List[concurrent.futures.Future]:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for arg in zip(*args):
            futures.append(executor.submit(func, *arg))

        concurrent.futures.wait(futures)
        for future in futures:
            future.result()

    return futures


def md5sum_of_file(filename) -> str:
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def exists(path) -> bool:
    return os.path.exists(path)


def get_audio_duration(audio_file):
    audio = AudioSegment.from_wav(audio_file)
    duration_seconds = len(audio) / 1000.0  # pydub calculates duration in milliseconds
    return duration_seconds
    