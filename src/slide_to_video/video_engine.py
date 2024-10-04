import os
import tempfile
from typing import List
import ffmpeg
from .utils import par_execute, get_audio_duration


def run_ffmpeg_command(command):
    command = command.global_args("-loglevel", "error")
    ffmpeg.run(command, overwrite_output=True)


class VideoEngine(object):
    """
    FFMPEG-based video utils.
    """

    def generate_video_from_image(
        self, image_path: str, video_path: str, duration: float
    ):
        print(f"Generating video from {image_path} with duration {duration}")
        # Load the image and set the duration
        input_image = ffmpeg.input(image_path, loop=1, t=duration, framerate=30)

        # Set the output file and parameters
        output = ffmpeg.output(
            input_image, video_path, vcodec="libx264", pix_fmt="yuv420p"
        )
        run_ffmpeg_command(output)

    def par_generate_video_from_image(
        self, image_paths: List[str], video_paths: List[str], durations: List[float]
    ):
        par_execute(self.generate_video_from_image, image_paths, video_paths, durations)

    def concatenate_videos(self, video_paths: List[str], output_path: str):
        print(f"Concatenating videos {video_paths} into {output_path}")

        # Create a temporary file listing all video files
        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", suffix=".txt"
        ) as temp_file:
            for video_path in video_paths:
                video_path = os.path.abspath(video_path)
                temp_file.write(f"file '{video_path}'\n")
            temp_file_path = temp_file.name

        # Concatenate videos using the concat demuxer
        output = ffmpeg.input(temp_file_path, format="concat", safe=0).output(
            output_path, c="copy"
        )
        run_ffmpeg_command(output)
        os.remove(temp_file_path)
        # inputs = [ffmpeg.input(video_path) for video_path in video_paths]
        # output = ffmpeg.concat(*inputs, v=1, a=1).node
        # output = ffmpeg.output(output[0], output_path, vcodec="copy", acodec="copy")
        # run_ffmpeg_command(output)

        # Prepare the input streams
        # inputs = [ffmpeg.input(video_path) for video_path in video_paths]

        # Create a stream for concatenation
        # video_streams = [input.video for input in inputs]
        # audio_streams = [input.audio for input in inputs]

        # Concatenate video and audio streams
        # concatenated_video = ffmpeg.concat(*video_streams, v=1, a=0).node
        # concatenated_audio = ffmpeg.concat(*audio_streams, v=0, a=1).node

        # Combine the concatenated video and audio streams
        # output = ffmpeg.output(concatenated_video[0], concatenated_audio[1], output_path, vcodec='copy', acodec='copy')

        # Run the ffmpeg command
        # run_ffmpeg_command(output)

    def add_audio_to_video(self, video_path, audio_path, output_path):
        input_video = ffmpeg.input(video_path)
        input_audio = ffmpeg.input(audio_path)

        output = ffmpeg.output(
            input_video,
            input_audio,
            output_path,
            vcodec="copy",
            acodec="aac",
            strict="experimental",
        )

        run_ffmpeg_command(output)

    def add_silence(self, input_file, duration: float = 2, direction="end"):
        # Get the suffix of the input file
        _, input_file_suffix = os.path.splitext(input_file)
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=input_file_suffix
        ) as temp_output_file:
            temp_output_file_name = temp_output_file.name

        try:
            # Generate 2 seconds of silence
            silence = ffmpeg.input(
                "anullsrc=channel_layout=5.1:sample_rate=48000", f="lavfi", t=duration
            )

            # Input audio file
            audio = ffmpeg.input(input_file)

            if direction == "end":
                output = ffmpeg.concat(audio, silence, v=0, a=1).output(
                    temp_output_file_name
                )
            elif direction == "start":
                output = ffmpeg.concat(silence, audio, v=0, a=1).output(
                    temp_output_file_name
                )
            else:
                raise ValueError(f"Invalid direction: {direction}")
            run_ffmpeg_command(output)

            os.replace(temp_output_file_name, input_file)
            print(f"Successfully added {duration} seconds of silence to {input_file}.")

        finally:
            # Clean up the temporary file if it still exists
            if os.path.exists(temp_output_file_name):
                os.remove(temp_output_file_name)

    def generate_subtitle_file(self, script_texts, durations, subtitle_path):
        """根据脚本文本生成字幕文件."""
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            for i, (text, duration) in enumerate(zip(script_texts, durations)):
                start_time = sum(durations[:i])
                end_time = start_time + duration
                f.write(f"{i + 1}\n")
                f.write(f"{self.format_time(start_time)} --> {self.format_time(end_time)}\n")
                f.write(f"{text}\n\n")

    def format_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02}:{minutes:02}:{int(seconds):02},{milliseconds:03}"
    
    def embed_subtitle(self, input_video_path, subtitle_path, output_video_path):
        input_video = ffmpeg.input(input_video_path)
        video_with_subtitle = input_video.video.filter('subtitles', subtitle_path)
        output = ffmpeg.output(
            video_with_subtitle,
            input_video.audio,
            output_video_path,
            vcodec='libx264',
            acodec='aac',
            strict='experimental',
            pix_fmt='yuv420p'
        )
        run_ffmpeg_command(output)