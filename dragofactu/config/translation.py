"""
Translation system for DRAGOFACTU
"""
import json
import os
from typing import Dict, Any
from functools import lru_cache

class TranslationManager:
    def __init__(self):
        self.current_language = "es"
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()
    
    def load_translations(self):
        """Load all translation files"""
        translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
        
        for lang_code in ['es', 'en', 'de']:
            file_path = os.path.join(translations_dir, f'{lang_code}.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            else:
                # Create default translation if file doesn't exist
                self.translations[lang_code] = {}
    
    def set_language(self, language_code: str):
        """Set current language"""
        if language_code in self.translations:
            self.current_language = language_code
            return True
        return False
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages"""
        return {
            'es': 'Español',
            'en': 'English', 
            'de': 'Deutsch'
        }
    
    @lru_cache(maxsize=1000)
    def t(self, key: str, **kwargs) -> str:
        """Get translated text"""
        translation = self.translations.get(self.current_language, {}).get(key, key)
        
        # Format with kwargs if provided
        if kwargs:
            try:
                return translation.format(**kwargs)
            except (KeyError, ValueError):
                return translation
        
        return translation
    
    def __call__(self, key: str, **kwargs) -> str:
        """Make the manager callable like t(key)"""
        return self.t(key, **kwargs)

# Global translation manager instance
translator = TranslationManager()

# Convenience function
def t(key: str, **kwargs) -> str:
    """Global translation function"""
    return translator.t(key, **kwargs)