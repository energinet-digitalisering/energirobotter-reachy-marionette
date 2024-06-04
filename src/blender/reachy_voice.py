import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd
import whisper


class ReachyVoice:

    def __init__(self):

        model_name = "medium.en"

        print("Initiating Whisper model: '" + model_name + "'...")
        self.model = whisper.load_model(model_name)
        print("Whisper model ready")

    def record_audio(self, duration, report_function, file_path=None):

        report_function({"INFO"}, "Recording...")

        samplerate = 44100
        recording = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="float32",
        )

        sd.wait()  # Wait until the recording is finished

        if file_path != None:
            wav.write(file_path, samplerate, recording)
            report_function({"INFO"}, "Recording saved to" + file_path)

        return recording.flatten()

    def transcribe_audio(self, audio_data=None, file_path=None, language="en"):

        if audio_data != None:
            # Normalise data
            audio_data = audio_data / np.max(np.abs(audio_data))

            # Convert the numpy array to the format expected by Whisper
            audio = whisper.pad_or_trim(audio_data)

            sd.play(audio)

            result = self.model.transcribe(audio, language=language, fp16=False)
            return result["text"]

        if file_path != None:
            # sd.play(file_path)

            result = self.model.transcribe(file_path, language=language)
            return result["text"]
