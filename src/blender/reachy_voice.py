from gtts import gTTS
import io
import numpy as np
import os
import pydub
import scipy.io.wavfile as wav
import sounddevice as sd
import whisper


class ReachyVoice:

    def __init__(self):

        model_name = "small"

        print("Initiating Whisper model: '" + model_name + "'...")
        self.model = whisper.load_model(model_name)
        print("Whisper model ready")

    def record_audio(self, file_path: str, duration, report_function):

        report_function({"INFO"}, "Recording...")

        samplerate = 44100
        recording = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="float32",
        )

        sd.wait()  # Wait until the recording is finished

        wav.write(file_path, samplerate, recording)
        report_function({"INFO"}, "Recording saved to " + str(file_path))

    def transcribe_audio(self, file_path: str, report_function, language="en"):

        if os.path.exists(file_path):
            result = self.model.transcribe(str(file_path), language=language)
            transcription = result["text"]

            report_function({"INFO"}, "Transcription: " + transcription)

            return transcription

        else:
            report_function(
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

        # Generate audio
        tts = gTTS(text=text, lang=language)

        audio, frame_rate = self.gtts_to_numpy(tts)

        sd.play(audio, frame_rate)
