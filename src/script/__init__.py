import typer
from typing import Optional
import yaml
import click
from slide_to_video.lib import slide_to_video
from slide_to_video.project import ProjectConfig
from slide_to_video.tts_engine.registery import get_all_engine_names


app = typer.Typer()


@app.command()
def generate(
    model: str = typer.Option(
        ...,
        help="Model to use. Use 'local' for local TTS engine or 'remote' for PlayHT TTS engine",
        case_sensitive=False,
        click_type=click.Choice(get_all_engine_names()),
    ),
    slide: str = typer.Option(..., help="Slide to use"),
    script: str = typer.Option(..., help="Script to use"),
    output_dir: str = typer.Option(..., help="Output directory"),
    voice: Optional[str] = typer.Option(
        None, help="Voice sample path or ID. Depends on the model."
    ),
    speech_speed: Optional[float] = typer.Option(
        None, help="Speed of the speech. Default value: 1.0."
    ),
    delay: Optional[float] = typer.Option(
        None, help="Delay between each slide in seconds. Default value: 2.0."
    ),
    script_dict: Optional[str] = typer.Option(
        None,
        help='Dictionary to replace the script. Each line should follow the format "original_text: new_text"',
    ),
    language: Optional[str] = typer.Option(
        None,
        case_sensitive=False,
        click_type=click.Choice(
            [
                "en",
                "es",
                "fr",
                "de",
                "it",
                "pt",
                "pl",
                "tr",
                "ru",
                "nl",
                "cs",
                "ar",
                "zh-cn",
                "hu",
                "ko",
                "ja",
                "hi",
            ]
        ),
        help="Language of the text. Default value: en.",
    ),
    config: Optional[str] = typer.Option(None, help="Path to yaml config file"),
    ctx: typer.Context = typer.Option(None),
):
    # Load the project config
    if config:
        with open(config, "r") as f:
            raw_config = yaml.safe_load(f)
    else:
        raw_config = {}
    for key, value in ctx.params.items():
        if value is not None:
            raw_config[key] = value
        elif key not in raw_config:
            if key == "speech_speed":
                raw_config[key] = 1.0
            elif key == "delay":
                raw_config[key] = 2.0
            elif key == "language":
                raw_config[key] = "en"

    project_config = ProjectConfig(raw_config)
    slide_to_video(project_config=project_config)


def main():
    app()
