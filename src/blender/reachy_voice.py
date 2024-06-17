import io
import numpy as np
import os
import scipy.io.wavfile as wav
import sounddevice as sd
import threading
import time

from gtts import gTTS
import pydub
import whisper


class ReachyVoice:

    def __init__(self):

        model_name = "small"

        print("Initiating Whisper model: '" + model_name + "'...")
        self.model = whisper.load_model(model_name)
        print("Whisper model ready")

        self.recording = False

    def record_audio(self, file_path: str, duartion_max=10.0):

        print("Recording...")

        samplerate = 44100
        audio_data = sd.rec(
            int(duartion_max * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="float32",
        )

        start_time = time.time()

        while self.recording:
            # Wait until the recording is finished or stopped

            current_time = time.time()
            elapsed_time = current_time - start_time

            if elapsed_time >= duartion_max:
                self.recording = False

        # Make sure recording is stopped, and data is trimmed to actual length (instead of duration_max)
        sd.stop()
        audio_data_trimmed = audio_data[: int(samplerate * elapsed_time)]

        # Clear file
        open(file_path, "wb").close()

        # Write new data
        wav.write(file_path, samplerate, audio_data_trimmed)
        print("Recording saved to " + str(file_path))

    def start_recording(self, report_blender, file_path: str, duration_max):

        if not self.recording:
            self.recording = True

            thread = threading.Thread(
                target=self.record_audio, args=[file_path, duration_max]
            )
            thread.start()

        else:
            report_blender({"INFO"}, "Recording is already in progress...")

    def stop_recording(self):
        self.recording = False

    def transcribe_audio(self, file_path: str, report_blender, language="en"):

        if os.path.exists(file_path):
            result = self.model.transcribe(str(file_path), language=language)
            transcription = result["text"]

            report_blender({"INFO"}, "Transcription: " + transcription)

            return transcription

        else:
            report_blender(
                {"ERROR"}, "File path '" + str(file_path) + "' does not exist."
            )

    def gtts_to_numpy(self, tts: gTTS):

        # Load into .mp3 format
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)  # Set buffer position at beginning

        # Read mp3 data
        audio = pydub.AudioSegment.from_file(mp3_fp, format="mp3")

        # Convert to NumPy array
        samples = np.array(audio.get_array_of_samples())

        # Normalize the audio data to the range [-1, 1]
        samples = samples / (2**15)

        return samples, audio.frame_rate

    def speak_audio(self, text: str, language="en"):

        if len(text) == 0:
            return

        # Generate audio
        tts = gTTS(text=text, lang=language)

        audio, frame_rate = self.gtts_to_numpy(tts)

        sd.play(audio, frame_rate)
