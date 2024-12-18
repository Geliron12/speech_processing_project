import wave
import json
from vosk import Model, KaldiRecognizer

class STT:
    
    def __init__(self, sample_rate=48000):
        '''Инициализация параметров модели'''
        model_path = r'./models/vosk/model/'
        self.model = Model(model_path)
        self.sample_rate = sample_rate
        self.rec = KaldiRecognizer(self.model, self.sample_rate)

    def wave_to_text(self, user_id):
        '''Функция, читающая wav файл и переводящая звук в текст'''
        with open(f"/stt_temp/user_{user_id}/input_{user_id}.wav", "rb") as f:
            while True:
                data = f.read(4000)
                if not data:
                    break
                self.rec.AcceptWaveform(data)
            result_json = self.rec.FinalResult()
            result = json.loads(result_json)
            return str(result['text'])
            

