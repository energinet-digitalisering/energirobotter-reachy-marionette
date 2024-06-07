import os
import scipy.io.wavfile as wav
import sounddevice as sd
import whisper


class ReachyVoice:

    def __init__(self):

        model_name = "medium"

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
        report_function({"INFO"}, "Recording saved to" + str(file_path))

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

    def speak_audio(self, text): ...
