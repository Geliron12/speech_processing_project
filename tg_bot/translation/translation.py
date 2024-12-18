from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

class TranslationModel:

    def __init__(self):
        '''Конструктор класса модели перевода'''
        model_name = 'facebook/nllb-200-distilled-600M'

        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to('cuda')
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.source_lang = 'rus_Cyrl'
        self.target_lang = 'eng_Latn'
        self.lang_mapping = {'en': 'eng_Latn', 'de': 'deu_Latn', 'es': 'spa_Latn'}

    def translate(self, text):
        '''Перевод текста на текущий целевой язык'''
        translator = pipeline('translation', model=self.model,
                                tokenizer=self.tokenizer,
                                src_lang=self.source_lang,
                                tgt_lang=self.target_lang)
        
        output = translator(text, max_length=512)
        translated_text = output[0]['translation_text']

        return translated_text
    
    def get_lang(self):
        '''Получение текущего языка'''
        return self.target_lang
    
    def change_lang(self, lang):
        '''Смена языка'''
        self.target_lang = self.lang_mapping[lang]