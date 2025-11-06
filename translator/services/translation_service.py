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
        
        # Supported languages
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
            'sw': 'Swahili',
            'yo': 'Yoruba',
            'ig': 'Igbo',
            'ha': 'Hausa',
            'am': 'Amharic',
            'so': 'Somali',
            'zu': 'Zulu',
            'xh': 'Xhosa',
            'rw': 'Kinyarwanda',
            'ny': 'Chichewa',
            'mg': 'Malagasy',
            'ln': 'Lingala',
            'sn': 'Shona',
            'st': 'Sesotho',
            'tn': 'Setswana',
        }
        
        # VERIFIED model mapping - Only models that actually exist
        self.model_mapping = {
            # European languages
            ('en', 'es'): 'Helsinki-NLP/opus-mt-en-es',
            ('es', 'en'): 'Helsinki-NLP/opus-mt-es-en',
            ('en', 'fr'): 'Helsinki-NLP/opus-mt-en-fr',
            ('fr', 'en'): 'Helsinki-NLP/opus-mt-fr-en',
            ('en', 'de'): 'Helsinki-NLP/opus-mt-en-de',
            ('de', 'en'): 'Helsinki-NLP/opus-mt-de-en',
            ('en', 'it'): 'Helsinki-NLP/opus-mt-en-it',
            ('it', 'en'): 'Helsinki-NLP/opus-mt-it-en',
            ('en', 'pt'): 'Helsinki-NLP/opus-mt-en-pt',
            ('pt', 'en'): 'Helsinki-NLP/opus-mt-pt-en',
            ('en', 'ru'): 'Helsinki-NLP/opus-mt-en-ru',
            ('ru', 'en'): 'Helsinki-NLP/opus-mt-ru-en',
            
            # Asian languages
            ('en', 'zh'): 'Helsinki-NLP/opus-mt-en-zh',
            ('zh', 'en'): 'Helsinki-NLP/opus-mt-zh-en',
            ('en', 'ja'): 'Helsinki-NLP/opus-mt-en-jap',
            ('ja', 'en'): 'Helsinki-NLP/opus-mt-jap-en',
            ('en', 'ko'): 'Helsinki-NLP/opus-mt-en-ko',
            ('ko', 'en'): 'Helsinki-NLP/opus-mt-ko-en',
            ('en', 'ar'): 'Helsinki-NLP/opus-mt-en-ar',
            ('ar', 'en'): 'Helsinki-NLP/opus-mt-ar-en',
            
            # VERIFIED African languages - English pairs
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
            
            # Zulu - using a different approach since direct model doesn't exist
            # ('en', 'zu'): 'Helsinki-NLP/opus-mt-en-zu',  # This model doesn't exist
            # ('zu', 'en'): 'Helsinki-NLP/opus-mt-zu-en',  # This model doesn't exist
            
            # Xhosa
            ('en', 'xh'): 'Helsinki-NLP/opus-mt-en-xh',
            ('xh', 'en'): 'Helsinki-NLP/opus-mt-xh-en',
            
            # Other verified African languages
            ('en', 'rw'): 'Helsinki-NLP/opus-mt-en-rw',
            ('rw', 'en'): 'Helsinki-NLP/opus-mt-rw-en',
            ('en', 'ny'): 'Helsinki-NLP/opus-mt-en-ny',
            ('ny', 'en'): 'Helsinki-NLP/opus-mt-ny-en',
            ('en', 'mg'): 'Helsinki-NLP/opus-mt-en-mg',
            ('mg', 'en'): 'Helsinki-NLP/opus-mt-mg-en',
            ('en', 'ln'): 'Helsinki-NLP/opus-mt-en-ln',
            ('ln', 'en'): 'Helsinki-NLP/opus-mt-ln-en',
            
            # Some direct European pairs
            ('es', 'fr'): 'Helsinki-NLP/opus-mt-es-fr',
            ('fr', 'es'): 'Helsinki-NLP/opus-mt-fr-es',
            ('de', 'fr'): 'Helsinki-NLP/opus-mt-de-fr',
            ('fr', 'de'): 'Helsinki-NLP/opus-mt-fr-de',
            ('es', 'pt'): 'Helsinki-NLP/opus-mt-es-pt',
            ('pt', 'es'): 'Helsinki-NLP/opus-mt-pt-es',
        }
        
        # Languages that don't have direct models - will use pivot translation
        self.unsupported_direct_languages = ['zu', 'sn', 'st', 'tn']
    
    def initialize(self):
        """Initialize only when needed"""
        if not self._initialized:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"Using device: {self.device}")
            self._initialized = True
    
    def get_model_name(self, source_lang, target_lang):
        """Get the appropriate model name for the language pair"""
        return self.model_mapping.get((source_lang, target_lang))
    
    def can_translate_directly(self, source_lang, target_lang):
        """Check if direct translation model exists"""
        # If either language is in unsupported list, cannot translate directly
        if source_lang in self.unsupported_direct_languages or target_lang in self.unsupported_direct_languages:
            return False
        return (source_lang, target_lang) in self.model_mapping
    
    def is_language_supported(self, lang_code):
        """Check if a language is supported (even if via pivot)"""
        return lang_code in self.supported_languages
    
    def load_model(self, source_lang, target_lang):
        """Lazy load translation model with better error handling"""
        self.initialize()
        
        model_key = f"{source_lang}_{target_lang}"
        
        if model_key not in self.models:
            model_name = self.get_model_name(source_lang, target_lang)
            if not model_name:
                raise ValueError(f"No direct translation model available for {source_lang} to {target_lang}")
            
            logger.info(f"Loading model: {model_name}")
            try:
                self.tokenizers[model_key] = MarianTokenizer.from_pretrained(model_name)
                self.models[model_key] = MarianMTModel.from_pretrained(model_name).to(self.device)
                self.models[model_key].eval()
                logger.info(f"Successfully loaded model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {str(e)}")
                # Remove the invalid model from mapping to prevent retries
                if (source_lang, target_lang) in self.model_mapping:
                    del self.model_mapping[(source_lang, target_lang)]
                raise Exception(f"Failed to load translation model: {str(e)}")
        
        return self.models[model_key], self.tokenizers[model_key]
    
    def translate_text(self, text, source_lang='en', target_lang='es', max_length=512):
        """Translate text with pivot translation if direct model not available"""
        # Create cache key
        cache_key = f"trans_{source_lang}_{target_lang}_{hash(text)}"
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for {source_lang}->{target_lang}")
            return cached_result
        
        try:
            start_time = time.time()
            
            # Case 1: Direct translation available
            if self.can_translate_directly(source_lang, target_lang):
                logger.info(f"Using direct translation: {source_lang}->{target_lang}")
                translated_text = self._direct_translate(text, source_lang, target_lang, max_length)
                translation_type = "direct"
            
            # Case 2: Pivot through English (for languages that don't have direct models)
            else:
                logger.info(f"Using pivot translation: {source_lang}->en->{target_lang}")
                translated_text = self._pivot_translate(text, source_lang, target_lang, max_length)
                translation_type = "pivot"
            
            translation_time = time.time() - start_time
            logger.info(f"Translation completed in {translation_time:.2f} seconds ({translation_type})")
            
            # Cache the result (5 minutes)
            cache.set(cache_key, translated_text, 300)
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation error {source_lang}->{target_lang}: {str(e)}")
            raise Exception(f"Translation failed: {str(e)}")
    
    def _direct_translate(self, text, source_lang, target_lang, max_length):
        """Direct translation using available model"""
        model, tokenizer = self.load_model(source_lang, target_lang)
        
        # Tokenize input
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate translation
        with torch.no_grad():
            translated = model.generate(**inputs, max_length=max_length)
        
        # Decode output
        translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
        return translated_text
    
    def _pivot_translate(self, text, source_lang, target_lang, max_length):
        """Two-step translation using English as pivot"""
        logger.info(f"Step 1: {source_lang} -> English")
        
        # Step 1: Source language -> English (if not already English)
        if source_lang != 'en':
            # For languages without direct models, we need to handle them specially
            if source_lang in self.unsupported_direct_languages:
                raise Exception(f"Translation from {source_lang} is not currently supported due to model limitations")
            
            english_text = self._direct_translate(text, source_lang, 'en', max_length)
        else:
            english_text = text
        
        # Step 2: English -> Target language (if not English)
        if target_lang != 'en':
            # For languages without direct models, we need to handle them specially
            if target_lang in self.unsupported_direct_languages:
                raise Exception(f"Translation to {target_lang} is not currently supported due to model limitations")
            
            logger.info(f"Step 2: English -> {target_lang}")
            final_text = self._direct_translate(english_text, 'en', target_lang, max_length)
        else:
            final_text = english_text
        
        return final_text
    
    def get_supported_languages(self):
        """Get list of supported languages"""
        return self.supported_languages
    
    def get_available_languages(self):
        """Get languages that have direct translation models"""
        available_langs = set()
        for source, target in self.model_mapping.keys():
            available_langs.add(source)
            available_langs.add(target)
        return {code: name for code, name in self.supported_languages.items() if code in available_langs}
    
    def get_translation_info(self, source_lang, target_lang):
        """Get information about translation path"""
        if source_lang in self.unsupported_direct_languages or target_lang in self.unsupported_direct_languages:
            return {
                'type': 'unsupported',
                'path': f'{source_lang} → {target_lang}',
                'description': f'Translation not available for this language pair',
                'available': False
            }
        elif self.can_translate_directly(source_lang, target_lang):
            return {
                'type': 'direct',
                'path': f'{source_lang} → {target_lang}',
                'description': 'Direct translation',
                'available': True
            }
        else:
            return {
                'type': 'pivot',
                'path': f'{source_lang} → English → {target_lang}',
                'description': 'Translation via English',
                'available': True
            }

# Global instance
translation_service = FastTranslationService()