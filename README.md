# slide-to-video

A tool that converts a slide deck into a video, complete with your voice narration. Support multiple languages.

## Installation
Tested on Ubuntu 20.04.

1. **Install `ffmpeg`**:
    ```bash
    sudo apt-get install ffmpeg
    ```
2. **Install Python (>=3.9 and <=3.11) and `pip`** if you haven't already.
3. **Clone and Install this Tool**:
    ```bash
    git clone git@github.com:Changochen/slide-to-video.git
    cd slide-to-video
    pip install .
    ```
4. **Verify Installation**:
    ```bash
    slide-to-video
    ```

## Preparation
1. **Slide Deck**: Create a slide deck in PDF format.
2. **Script**: Prepare a script file in plain text format, with slides separated by the marker `NEWSLIDE`.
3. **Audio File or Model**: Record an audio file of your voice in MP3 format for voice cloning. If you use paid services like Play.ht, you should have a voice model available.

## Usage
```bash
slide-to-video --model MODEL_NAME --slide slide --script script --output-dir OUTPUT_PATH --config ADDITIONAL_CONFIG.yaml
```
A final video will be generated in the `OUTPUT_PATH` directory as `output.mp4`.


https://github.com/Changochen/slide-to-video/assets/18531282/c774367b-e585-4885-b13d-78940934a422


For more options, including adjusting speech speed, run:
```bash
slide-to-video --help
```

**Currently Supported Model**:
1. [TTS](https://github.com/coqui-ai/TTS)
2. [play.ht](https://play.ht/)

**Currently Supported Languages**:
'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn', 'hu', 'ko', 'ja', 'hi'

### Example Usage
To use a local voice model:
```bash
slide-to-video --model local --slide example/slide.pdf --script example/script.txt --voice example/sample.mp3 --output-dir output
```

After a few seconds, you will see a video file `output.mp4` in the `output` directory.

## Cached Regeneration
After generating the video, the output directory will contain a `project.yaml` file, which helps skip the generation of unchanged content. If inputs remain the same, the tool skips the video generation process.

### To Force Regeneration
If you modify the slide, script, or settings (like speech speed), the tool regenerates the affected content. To force regeneration of specific parts, set the `force_reset` field of the corresponding item in `project.yaml` in the output directory.

### Support a new voice model
To support a new voice model, you need to implement a new class in `src/slide_to_video/tts_engine` and register the class by calling `x` (See an example at (here)[src/slide_to_video/tts_engine/local.py]).

## Notes
1. On the first run, you might see the following prompt:
    ```
    > You must confirm the following:
    | > "I have purchased a commercial license from Coqui: licensing@coqui.ai"
    | > "Otherwise, I agree to the terms of the non-commercial CPML: https://coqui.ai/cpml" - [y/n]
    | | > 
    ```
    Simply enter `y`.
