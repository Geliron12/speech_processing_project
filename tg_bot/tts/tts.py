import os
import torch

class TTS:
    '''Класс, реализующий логику работы с TTS моделью'''
    def __init__(self, device='cpu', sample_rate=48000, language='en'):
        '''Конструктор'''
        self.device = device
        self.sample_rate = sample_rate
        self.load_model_by_language(language)
        self.lang = language

    def text_to_speech(self, text, user_id):
        '''Переводим текст в аудио и сохраняем во временный файл'''
        path = f'/stt_temp/user_{user_id}/{user_id}_tts.wav'
        if os.path.exists(path):
            os.remove(path)
        self.model.save_wav(audio_path= path,text=text, speaker=self.speaker, sample_rate=self.sample_rate)
        
    def load_model_by_language(self, lang='en'):
        '''Подгружаем модель с нужным языком'''
        device = torch.device(self.device)
        local_file = f'./models/tts/model_{lang}.pt'
        if not os.path.isfile(local_file):
            torch.hub.download_url_to_file(f'https://models.silero.ai/models/tts/{lang}/v3_{lang}.pt',
                                   local_file)  
        self.model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
        self.model.to(device)
        if lang == 'es':
            self.speaker = 'es_2'
        elif lang == 'de':
            self.speaker = 'karlsson'
        else:
            self.speaker = 'en_15'

    def get_current_language(self):
        return self.lang
    
    def change_language(self, lang='en'):
        if lang == self.lang:
            return
        self.load_model_by_language(lang)