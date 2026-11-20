"""Render original, captioned chart cards as a vertical H.264 clip."""

from decimal import Decimal
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory


FRAME_SIZE = (720, 1280)
SCENE_SECONDS = (4, 6, 5)
NO_BREAK_SPACE = "\N{NO-BREAK SPACE}"


def render(draft, maximum, cues, font_file):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:
        raise ValueError("install Pillow to render a Short") from error
    if draft["locale"] != "en" and font_file is None:
        raise ValueError("provide a font with glyphs for the draft locale using --font-file")

    def font(size):
        return ImageFont.truetype(str(font_file), size) if font_file else ImageFont.load_default(size=size)

    story = draft["story"]
    claim, = story["claims"]
    value, unit = claim["value"], claim["unit"]
    chart_width = 540
    accent = "#6ff0c0"
    paper = "#f2f8f4"
    muted = "#aac5bc"

    with TemporaryDirectory(prefix="fastest-short-") as staging:
        frames = Path(staging)
        for index, cue in enumerate(cues):
            image = Image.new("RGB", FRAME_SIZE, "#102a29")
            draw = ImageDraw.Draw(image)

            def text(position, words, size, fill=paper, lines=1):
                # Reserve the right edge and lower margin for platform overlays.
                for selected_size in range(size, 19, -2):
                    face = font(selected_size)
                    available = 600 - position[0]
                    wrapped = _wrap(words, face, available, draft["locale"])
                    if len(wrapped) <= lines and all(face.getlength(line) <= available for line in wrapped):
                        draw.multiline_text(position, "\n".join(wrapped), font=face, fill=fill, spacing=12)
                        return
                raise ValueError("benchmark copy is too long to fit the video")

            text((56, 120), "fastest.ai", 32, accent)
            draw.line((56, 182, 596, 182), fill="#395654", width=2)
            if index == 1:
                text((56, 282), story["copy"]["headline"], 44, lines=3)
                text((56, 485), f"{value} {unit}", 58, accent)
                draw.rounded_rectangle((56, 590, 595, 647), 10, fill="#395654")
                filled = round(chart_width * Decimal(value) / Decimal(maximum))
                if filled:
                    draw.rounded_rectangle((56, 590, 55 + filled, 647), min(10, filled // 2), fill=accent)
                text((56, 671), f"0 / {maximum} {unit}", 27, muted)
            else:
                headline = story["copy"]["headline"] if index == 0 else cue
                text((56, 345), headline, 60, lines=4)
            if index != 2:
                draw.rounded_rectangle((40, 870, 622, 1090), 18, fill="#071816")
                caption = cue.replace(f"{value} {unit}", f"{value}{NO_BREAK_SPACE}{unit}")
                text((56, 898), caption, 36, lines=4)
            image.save(frames / f"{index}.png")

        playlist = "\n".join(
            f"file '{index}.png'\nduration {seconds}" for index, seconds in enumerate(SCENE_SECONDS)
        )
        (frames / "frames.txt").write_text(f"{playlist}\nfile '{len(cues) - 1}.png'\n", encoding="ascii")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-nostdin", "-v", "error", "-f", "concat", "-i", "frames.txt",
                    "-vf", "fps=24,format=yuv420p", "-t", str(sum(SCENE_SECONDS)),
                    "-c:v", "libx264", "-threads", "2", "-movflags", "+faststart", "short.mp4",
                ],
                cwd=frames, check=True, capture_output=True, text=True, timeout=60,
            )
        except FileNotFoundError as error:
            raise ValueError("install ffmpeg with libx264 to render a Short") from error
        except subprocess.CalledProcessError as error:
            raise ValueError(f"ffmpeg failed to render the Short: {error.stderr.strip()}") from error
        except subprocess.TimeoutExpired as error:
            raise ValueError("ffmpeg timed out rendering the Short") from error
        return (frames / "short.mp4").read_bytes()


def _wrap(text, font, width, locale):
    # Keep numbers, their units, and closing punctuation together.
    if locale == "en":
        words = text.split(" ")
    else:
        words = re.findall(r"(?:[a-zA-Z0-9./\u00a0]+|.)[，。？！、：；）】》」』]*", text)
    lines, line = [], ""
    for word in words:
        candidate = f"{line} {word}" if line and locale == "en" else line + word
        if line and font.getlength(candidate.replace(NO_BREAK_SPACE, " ")) > width:
            lines.append(line.rstrip())
            line = word.lstrip()
        else:
            line = candidate
    return [entry.replace(NO_BREAK_SPACE, " ") for entry in (*lines, line.rstrip())]
