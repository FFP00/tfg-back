import shutil
import subprocess
import tempfile
from pathlib import Path

_FFMPEG = shutil.which("ffmpeg") or "/tmp/ffmpeg"


def convert_video(data: bytes, max_duration: int | None = None) -> bytes | None:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "input"
        dst = Path(tmp) / "output.mp4"
        src.write_bytes(data)
        cmd = [_FFMPEG, "-y", "-i", str(src)]
        if max_duration:
            cmd += ["-t", str(max_duration)]
        cmd += [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "35",
            "-vf", "scale=-2:1080",
            "-c:a", "aac", "-b:a", "64k", "-ac", "1",
            str(dst),
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0 or not dst.exists():
            return None
        return dst.read_bytes()
