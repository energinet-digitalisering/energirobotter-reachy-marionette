import numpy as np
import sounddevice as sd
import whisper


class ReachyVoice:

    def __init__(self):

        model_name = "large"

        print("Initiating Whisper model: '" + model_name + "'...")
        self.model = whisper.load_model(model_name)
        print("Whisper model ready")

    def record_audio(self, duration, report_function):

        report_function({"INFO"}, "Recording...")

        samplerate = 44100
        recording = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="float32",
        )
        sd.wait()  # Wait until the recording is finished

        report_function({"INFO"}, "Recording stopped")

        return recording.flatten()

    def transcribe_audio(self, audio_data, language="en"):

        # Normalise data
        audio_data = audio_data / np.max(np.abs(audio_data))

        # Convert the numpy array to the format expected by Whisper
        audio = whisper.pad_or_trim(audio_data)

        sd.play(audio)

        result = self.model.transcribe(audio, language=language, fp16=False)

        return result["text"]
