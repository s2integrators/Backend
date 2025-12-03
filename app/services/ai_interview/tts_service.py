import subprocess
import tempfile
import os

class TTSService:
    def synthesize(self, text: str) -> bytes:
        # macOS "say" outputs AIFF, so temporary AIFF file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".aiff") as tmp:
            aiff_path = tmp.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp2:
            wav_path = tmp2.name

        try:
            # generate AIFF audio
            cmd = [
                "say",
                "-v", "Samantha",
                "-o", aiff_path,
                text
            ]
            subprocess.run(cmd, capture_output=True)

            # convert AIFF → WAV using ffmpeg
            convert_cmd = [
                "ffmpeg",
                "-y",
                "-i", aiff_path,
                "-ac", "1",
                "-ar", "22050",
                wav_path
            ]
            subprocess.run(convert_cmd, capture_output=True)

            # read the WAV file
            with open(wav_path, "rb") as f:
                return f.read()

        finally:
            for p in [aiff_path, wav_path]:
                if os.path.exists(p):
                    os.unlink(p)
