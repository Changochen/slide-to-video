from __future__ import annotations
import enum
from multiprocessing import Manager

from .utils import md5sum_of_file, exists, get_audio_duration, get_video_duration
import yaml
from .slide_engine import SlideEngine
from .script_engine import ScriptEngine
from .tts_engine import TTSEngine, create_engine
from .video_engine import VideoEngine
import concurrent.futures



class TargetVoice:
    def __init__(self, *, model=None, audio=None):
        self.model = model
        self.audio = audio


class ItemType(enum.Enum):
    SLIDE = "slide"
    SCRIPT = "script"
    VOICE = "voice"
    VIDEO = "video"


class Item:
    def __init__(
        self, *, path, type, extra=None, md5sum=None, cached=False, force_reset=False
    ):
        self.path = path
        self.type = type
        self.cached = cached
        if not md5sum:
            md5sum = md5sum_of_file(path)
        self.md5sum = md5sum
        if extra:
            extra = dict(extra)
        self.extra = extra
        self.force_reset = force_reset

    def reset(self):
        self.cached = False

    @property
    def content(self):
        with open(self.path, "r") as f:
            return f.read()

    def __eq__(self, other: object):
        if not isinstance(other, Item):
            return False
        return self.md5sum == other.md5sum and self.extra == other.extra

    def cache(self):
        self.cached = True

    @staticmethod
    def from_yaml(data) -> Item:
        return Item(
            path=data["path"],
            type=ItemType(data["type"]),
            cached=data["cached"],
            md5sum=data["md5sum"],
            force_reset=data.get("force_reset", False),
            extra=data.get("extra", None),
        )

    def to_yaml(self):
        result = {
            "path": self.path,
            "type": self.type.value,
            "cached": self.cached,
            "md5sum": self.md5sum,
            "force_reset": self.force_reset,
        }
        if self.extra:
            result["extra"] = self.extra
        return result


class Task(object):
    def __init__(
        self,
        *,
        id,
        slide: Item,
        script: Item,
        output_dir,
        tts_engine: TTSEngine,
        delay: float,
        lock=None,
    ):
        self.id = id
        self.slide = slide
        self.script = script
        self.output_dir = output_dir
        self.tts_engine = tts_engine
        self.lock = lock
        self.delay = delay

    def build(self):
        video_file = f"{self.output_dir}/sub_paragraph_without_sound_{self.id}.mp4"
        audio_file = f"{self.output_dir}/sub_paragraph_{self.id}.wav"
        final_video_file = f"{self.output_dir}/sub_paragraph_{self.id}.mp4"
        #添加字幕
        subtitle_file = f"{self.output_dir}/sub_paragraph_{self.id}.srt"
         
        if self.script.cached and self.slide.cached:
            return

        if not self.script.cached:
            if self.lock:
                self.lock.acquire()
            self.tts_engine.synthesize(self.script.content, audio_file)
            if self.lock:
                self.lock.release()
        video_engine = VideoEngine()
        if self.id != 1:
            video_engine.add_silence(audio_file, self.delay / 2, direction="start")
        end_delay = self.delay / 2
        if self.script.extra:
            end_delay = self.script.extra.get("delay", end_delay)
        video_engine.add_silence(audio_file, end_delay, direction="end")

        duration = get_audio_duration(audio_file)

        if not self.slide.cached or self.script.cached:
            video_engine.generate_video_from_image(
                self.slide.path, video_file, duration
            )
            # video_engine.add_audio_to_video(video_file, audio_file, final_video_file)

            # # 生成字幕文件
            # self.generate_subtitle(self.script.content, subtitle_file, duration, start_delay, end_delay)
            # # 合成视频、音频和字幕
            # video_engine.add_audio_and_subtitle_to_video(
            #     video_file, audio_file, subtitle_file, final_video_file
            # )
             # 生成字幕文件
            script_texts = [self.script.content]  # 将内容转为列表
            video_engine.generate_subtitle_file(script_texts, [duration], subtitle_file)

            # 合成视频、音频和字幕
            video_engine.add_audio_and_subtitle_to_video(
                video_file, audio_file, script_texts, final_video_file
            )

class ProjectConfig(dict):
    def __init__(self, config):
        super().__init__()
        skip_keywords = ["config"]
        for key, value in config.items():
            if key not in skip_keywords:
                self[key] = value
        self.validate()

    def as_dict(self):
        return dict(self)

    def validate(self):
        required_fields = [
            "model",
            "slide",
            "script",
            "output_dir",
            "speech_speed",
            "delay",
        ]

        for field in required_fields:
            if field not in self.keys():
                raise ValueError(f"Missing required field {field}")


class Project:
    def __init__(
        self,
        *,
        name,
        config: ProjectConfig,
        from_file=False,
    ):
        self.name = name
        self.slide = config["slide"]
        self.script = config["script"]
        self.output_dir = config["output_dir"]
        self.config = config
        self.slide_items = []
        self.script_items = []
        self.speech_speed = config["speech_speed"]

        if not from_file:
            self.calculate_items()
            project_file = f"{self.output_dir}/project.yaml"
            previous_project = self.load_project_file(project_file)
            if previous_project:
                self.sync_project(previous_project)

    def all_reset(self):
        for item in self.slide_items:
            item.reset()
        for item in self.script_items:
            item.reset()

    def sync_project(self, previous_project: Project):
        if (
            self.config.as_dict() != previous_project.config.as_dict()
            or self.speech_speed != previous_project.speech_speed
            or len(self.slide_items) != len(previous_project.slide_items)
        ):
            self.all_reset()
            return

        for i in range(len(self.slide_items)):
            self.slide_items[i].force_reset = previous_project.slide_items[
                i
            ].force_reset
            self.script_items[i].force_reset = previous_project.script_items[
                i
            ].force_reset
            if (
                self.slide_items[i] == previous_project.slide_items[i]
                and not previous_project.slide_items[i].force_reset
            ):
                self.slide_items[i].cached = True
            if (
                self.script_items[i] == previous_project.script_items[i]
                and not previous_project.script_items[i].force_reset
            ):
                self.script_items[i].cached = True

    def calculate_items(self):
        slide_engine = SlideEngine()
        images = slide_engine.slide_to_images(self.slide, self.output_dir)
        sorted_images = sorted(images)
        self.slide_items = [
            Item(path=image, type=ItemType.SLIDE) for image in sorted_images
        ]
        self.script_items = [
            Item(path=script.path, type=ItemType.SCRIPT, extra=script.config)
            for script in ScriptEngine().split_script(
                self.script,
                self.output_dir,
                script_dict=self.config.get("script_dict", None),
            )
        ]

        assert len(self.slide_items) == len(self.script_items)

    def load_project_file(self, project_file):
        if exists(project_file):
            with open(project_file, "r") as f:
                project_data = yaml.safe_load(f)

                slide = project_data.get("slide")
                script = project_data.get("script")
                output_dir = project_data.get("output_dir")
                config = project_data.get("config")
                speech_speed = project_data.get("speech_speed")
                slide_items = []
                for slide_item in project_data.get("slide_items"):
                    slide_items.append(Item.from_yaml(slide_item))
                script_items = []
                for script_item in project_data.get("script_items"):
                    script_items.append(Item.from_yaml(script_item))

                config["slide"] = slide
                config["script"] = script
                config["output_dir"] = output_dir
                config["speech_speed"] = speech_speed
                project_config = ProjectConfig(config)

                project = Project(
                    name=self.name,
                    config=project_config,
                    from_file=True,
                )

                project.slide_items = slide_items
                project.script_items = script_items

                return project

        return None

    def to_yaml(self):
        # Create a yaml representation of the project
        return {
            "name": self.name,
            "slide": self.slide,
            "script": self.script,
            "output_dir": self.output_dir,
            "speech_speed": self.speech_speed,
            "config": self.config.as_dict(),
            "slide_items": [slide_item.to_yaml() for slide_item in self.slide_items],
            "script_items": [
                script_item.to_yaml() for script_item in self.script_items
            ],
        }

    def save(self):
        project_file = f"{self.output_dir}/project.yaml"
        with open(project_file, "w") as f:
            yaml.dump(self.to_yaml(), f, sort_keys=False)

    def get_images(self, filter_cached=False):
        if filter_cached:
            return [item.path for item in self.slide_items if not item.cached]
        return [item.path for item in self.slide_items]

    def get_scripts(self, filter_cached=False):
        if filter_cached:
            return [item.content for item in self.script_items if not item.cached]
        return [item.content for item in self.script_items]

    def build(self):
        model = self.config.get("model")
        assert model
        tts_engine = create_engine(model, self.config)
        lock = None
        if not tts_engine.parallizable():
            manager = Manager()
            lock = manager.Lock()
        futures = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            tasks = []
            for i in range(len(self.slide_items)):
                task = Task(
                    id=i + 1,
                    slide=self.slide_items[i],
                    script=self.script_items[i],
                    output_dir=self.output_dir,
                    tts_engine=tts_engine,
                    lock=lock,
                    delay=self.config["delay"],
                )
                tasks.append(task)
                futures.append(executor.submit(task.build))

        for future in futures:
            future.result()

        cached_script_list = [item.cached for item in self.script_items]
        cached_slide_list = [item.cached for item in self.slide_items]

        # if not all(cached_script_list) or not all(cached_slide_list):
        #     video_engine = VideoEngine()
        #     video_paths = [
        #         f"{self.output_dir}/sub_paragraph_{i+1}.mp4"
        #         for i in range(len(self.slide_items))
        #     ]
        #     final_output = f"{self.output_dir}/output.mp4"

        #     video_engine.concatenate_videos(video_paths, final_output)
        # else:
        #     print("All items are cached. No need to build the project.")

        if not all(cached_script_list) or not all(cached_slide_list):
            video_engine = VideoEngine()
            video_paths = [
                f"{self.output_dir}/sub_paragraph_{i+1}.mp4"
                for i in range(len(self.slide_items))
            ]
            final_output = f"{self.output_dir}/output.mp4"

            video_engine.concatenate_videos(video_paths, final_output)

            # 合并字幕文件
            subtitle_paths = [
                f"{self.output_dir}/sub_paragraph_{i+1}.srt"
                for i in range(len(self.script_items))
            ]

            # 将字幕嵌入最终视频
            final_output_with_subtitles = f"{self.output_dir}/output_with_subtitles.mp4"
            video_engine.embed_subtitle(final_output, subtitle_paths, final_output_with_subtitles)
        else:
            print("All items are cached. No need to build the project.")