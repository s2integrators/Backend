import subprocess
import tempfile
import os

class STTService:
    def transcribe(self, audio_bytes: bytes) -> str:

        # Step 1: Save input bytes to temp file (unknown format)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".input") as tmp:
            tmp.write(audio_bytes)
            temp_input_path = tmp.name

        # Step 2: Create real WAV file (16kHz mono)
        temp_wav_path = temp_input_path + ".wav"

        try:
            # ffmpeg converts to clean WAV
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", temp_input_path,
                "-ac", "1",
                "-ar", "16000",
                temp_wav_path
            ]
            subprocess.run(ffmpeg_cmd, capture_output=True)

            output_txt_path = temp_wav_path + ".txt"

            # Step 3: Run whisper-cli on converted wav
            whisper_cmd = [
                "whisper-cli",
                "-m", os.path.expanduser("~/.whisper/ggml-medium.en.bin"),
                "-f", temp_wav_path,
                "-otxt"
            ]
            result = subprocess.run(whisper_cmd, capture_output=True, text=True)

            print("DEBUG:", result.stdout)
            print("DEBUG ERR:", result.stderr)

            # Step 4: read transcription
            if os.path.exists(output_txt_path):
                with open(output_txt_path, "r") as f:
                    return f.read().strip()

            return ""

        finally:
            # cleanup
            for p in [temp_input_path, temp_wav_path, temp_wav_path + ".txt"]:
                if os.path.exists(p):
                    os.unlink(p)
