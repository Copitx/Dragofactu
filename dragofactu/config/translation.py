"""
Translation system for DRAGOFACTU
Supports: Spanish (es), English (en), German (de)
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

# User settings file location
USER_SETTINGS_DIR = Path.home() / ".dragofactu" / "config"
USER_SETTINGS_FILE = USER_SETTINGS_DIR / "settings.json"


def load_user_settings() -> Dict[str, Any]:
    """Load user settings from file"""
    if USER_SETTINGS_FILE.exists():
        try:
            with open(USER_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_user_settings(settings: Dict[str, Any]):
    """Save user settings to file"""
    try:
        USER_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(USER_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: Could not save settings: {e}")


class TranslationManager:
    _instance = None
    _cache: Dict[str, str] = {}

    def __new__(cls):
        """Singleton pattern to ensure one instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()

        # Load saved language preference or default to Spanish
        settings = load_user_settings()
        self.current_language = settings.get('language', 'es')

        # Validate language exists
        if self.current_language not in self.translations:
            self.current_language = 'es'

    def load_translations(self):
        """Load all translation files"""
        translations_dir = os.path.join(os.path.dirname(__file__), 'translations')

        for lang_code in ['es', 'en', 'de']:
            file_path = os.path.join(translations_dir, f'{lang_code}.json')
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Could not load {lang_code}.json: {e}")
                    self.translations[lang_code] = {}
            else:
                self.translations[lang_code] = {}

    def set_language(self, language_code: str) -> bool:
        """Set current language and save preference"""
        if language_code not in self.translations:
            return False

        self.current_language = language_code

        # Clear translation cache
        self._cache.clear()

        # Save preference to user settings
        settings = load_user_settings()
        settings['language'] = language_code
        save_user_settings(settings)

        return True

    def get_language(self) -> str:
        """Get current language code"""
        return self.current_language

    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages with display names"""
        return {
            'es': 'Español',
            'en': 'English',
            'de': 'Deutsch'
        }

    def t(self, key: str, **kwargs) -> str:
        """Get translated text for key (supports nested keys like 'menu.dashboard')"""
        # Check cache first
        cache_key = f"{self.current_language}:{key}"
        if cache_key in self._cache and not kwargs:
            return self._cache[cache_key]

        # Navigate nested dictionary with dot notation
        translation = self.translations.get(self.current_language, {})
        for part in key.split('.'):
            if isinstance(translation, dict):
                translation = translation.get(part, key)
            else:
                translation = key
                break

        # If we got a dict instead of string, return the key
        if isinstance(translation, dict):
            translation = key

        # Format with kwargs if provided
        if kwargs:
            try:
                return translation.format(**kwargs)
            except (KeyError, ValueError):
                return translation

        # Cache the result
        self._cache[cache_key] = translation
        return translation

    def __call__(self, key: str, **kwargs) -> str:
        """Make the manager callable like t(key)"""
        return self.t(key, **kwargs)


# Global translation manager instance (singleton)
translator = TranslationManager()


# Convenience function
def t(key: str, **kwargs) -> str:
    """Global translation function"""
    return translator.t(key, **kwargs)
