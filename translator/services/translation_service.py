import torch
from transformers import MarianMTModel, MarianTokenizer
from django.core.cache import cache
import logging
import time

logger = logging.getLogger(__name__)

class FastTranslationService:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.device = None
        self._initialized = False
        
        # Supported languages - Including African languages and Chichewa
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            
            # African Languages
            'sw': 'Swahili',
            'yo': 'Yoruba',
            'ig': 'Igbo',
            'ha': 'Hausa',
            'am': 'Amharic',
            'so': 'Somali',
            'zu': 'Zulu',
            'xh': 'Xhosa',
            'rw': 'Kinyarwanda',
            'ny': 'Chichewa',  # Chichewa/Nyanja
            'mg': 'Malagasy',
            'ln': 'Lingala',
            'sn': 'Shona',
            'st': 'Sesotho',
            'tn': 'Setswana',
        }
        
        # Model mapping - Added African language pairs
        self.model_mapping = {
            # Existing European/Asian languages
            ('en', 'es'): 'Helsinki-NLP/opus-mt-en-es',
            ('es', 'en'): 'Helsinki-NLP/opus-mt-es-en',
            ('en', 'fr'): 'Helsinki-NLP/opus-mt-en-fr',
            ('fr', 'en'): 'Helsinki-NLP/opus-mt-fr-en',
            ('en', 'de'): 'Helsinki-NLP/opus-mt-en-de',
            ('de', 'en'): 'Helsinki-NLP/opus-mt-de-en',
            ('en', 'zh'): 'Helsinki-NLP/opus-mt-en-zh',
            ('zh', 'en'): 'Helsinki-NLP/opus-mt-zh-en',
            ('en', 'ja'): 'Helsinki-NLP/opus-mt-en-jap',
            ('ja', 'en'): 'Helsinki-NLP/opus-mt-jap-en',
            ('en', 'ko'): 'Helsinki-NLP/opus-mt-en-ko',
            ('ko', 'en'): 'Helsinki-NLP/opus-mt-ko-en',
            ('en', 'ar'): 'Helsinki-NLP/opus-mt-en-ar',
            ('ar', 'en'): 'Helsinki-NLP/opus-mt-ar-en',
            
            # African Languages - English to African
            ('en', 'sw'): 'Helsinki-NLP/opus-mt-en-swc',
            ('sw', 'en'): 'Helsinki-NLP/opus-mt-swc-en',
            ('en', 'yo'): 'Helsinki-NLP/opus-mt-en-yo',
            ('yo', 'en'): 'Helsinki-NLP/opus-mt-yo-en',
            ('en', 'ig'): 'Helsinki-NLP/opus-mt-en-ig',
            ('ig', 'en'): 'Helsinki-NLP/opus-mt-ig-en',
            ('en', 'ha'): 'Helsinki-NLP/opus-mt-en-ha',
            ('ha', 'en'): 'Helsinki-NLP/opus-mt-ha-en',
            ('en', 'am'): 'Helsinki-NLP/opus-mt-en-am',
            ('am', 'en'): 'Helsinki-NLP/opus-mt-am-en',
            ('en', 'so'): 'Helsinki-NLP/opus-mt-en-so',
            ('so', 'en'): 'Helsinki-NLP/opus-mt-so-en',
            ('en', 'zu'): 'Helsinki-NLP/opus-mt-en-zu',
            ('zu', 'en'): 'Helsinki-NLP/opus-mt-zu-en',
            ('en', 'xh'): 'Helsinki-NLP/opus-mt-en-xh',
            ('xh', 'en'): 'Helsinki-NLP/opus-mt-xh-en',
            ('en', 'rw'): 'Helsinki-NLP/opus-mt-en-rw',
            ('rw', 'en'): 'Helsinki-NLP/opus-mt-rw-en',
            ('en', 'ny'): 'Helsinki-NLP/opus-mt-en-ny',  # Chichewa
            ('ny', 'en'): 'Helsinki-NLP/opus-mt-ny-en',  # Chichewa
            ('en', 'mg'): 'Helsinki-NLP/opus-mt-en-mg',
            ('mg', 'en'): 'Helsinki-NLP/opus-mt-mg-en',
            ('en', 'ln'): 'Helsinki-NLP/opus-mt-en-ln',
            ('ln', 'en'): 'Helsinki-NLP/opus-mt-ln-en',
            ('en', 'sn'): 'Helsinki-NLP/opus-mt-en-sn',
            ('sn', 'en'): 'Helsinki-NLP/opus-mt-sn-en',
            ('en', 'st'): 'Helsinki-NLP/opus-mt-en-st',
            ('st', 'en'): 'Helsinki-NLP/opus-mt-st-en',
            ('en', 'tn'): 'Helsinki-NLP/opus-mt-en-tn',
            ('tn', 'en'): 'Helsinki-NLP/opus-mt-tn-en',
            
            # Some African language pairs
            ('fr', 'sw'): 'Helsinki-NLP/opus-mt-fr-swc',
            ('sw', 'fr'): 'Helsinki-NLP/opus-mt-swc-fr',
            ('fr', 'mg'): 'Helsinki-NLP/opus-mt-fr-mg',
            ('mg', 'fr'): 'Helsinki-NLP/opus-mt-mg-fr',
        }
    
    def initialize(self):
        """Initialize only when needed"""
        if not self._initialized:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"Using device: {self.device}")
            self._initialized = True
    
    def get_model_name(self, source_lang, target_lang):
        return self.model_mapping.get((source_lang, target_lang))
    
    def load_model(self, source_lang, target_lang):
        """Lazy load model"""
        self.initialize()
        
        model_key = f"{source_lang}_{target_lang}"
        
        if model_key not in self.models:
            model_name = self.get_model_name(source_lang, target_lang)
            if not model_name:
                raise ValueError(f"Translation from {source_lang} to {target_lang} not supported")
            
            logger.info(f"Loading model: {model_name}")
            try:
                self.tokenizers[model_key] = MarianTokenizer.from_pretrained(model_name)
                self.models[model_key] = MarianMTModel.from_pretrained(model_name).to(self.device)
                self.models[model_key].eval()
                logger.info(f"Successfully loaded model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {str(e)}")
                raise Exception(f"Failed to load translation model: {str(e)}")
        
        return self.models[model_key], self.tokenizers[model_key]
    
    def translate_text(self, text, source_lang='en', target_lang='es'):
        """Translate text with caching"""
        # Cache key
        cache_key = f"trans_{source_lang}_{target_lang}_{hash(text)}"
        
        # Check cache
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            model, tokenizer = self.load_model(source_lang, target_lang)
            
            # Tokenize
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                translated = model.generate(**inputs, max_length=512)
            
            # Decode
            translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
            
            # Cache for 5 minutes
            cache.set(cache_key, translated_text, 300)
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise Exception(f"Translation failed: {str(e)}")
    
    def get_supported_languages(self):
        return self.supported_languages
    
    def get_african_languages(self):
        """Get only African languages"""
        african_codes = ['sw', 'yo', 'ig', 'ha', 'am', 'so', 'zu', 'xh', 'rw', 'ny', 'mg', 'ln', 'sn', 'st', 'tn']
        return {code: name for code, name in self.supported_languages.items() if code in african_codes}
    
    def get_language_families(self):
        """Get languages grouped by region/family"""
        return {
            'european': {k: v for k, v in self.supported_languages.items() if k in ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru']},
            'asian': {k: v for k, v in self.supported_languages.items() if k in ['zh', 'ja', 'ko', 'ar']},
            'african': self.get_african_languages()
        }

# Global instance
translation_service = FastTranslationService()