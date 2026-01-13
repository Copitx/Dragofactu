"""
Translation system for DRAGOFACTU
Supports dynamic language switching without application restart.
"""
import json
import os
from typing import Dict, Any, List, Callable, Optional
from PySide6.QtCore import QObject, Signal


class TranslationManager(QObject):
    """
    Translation manager with dynamic language switching support.
    Emits language_changed signal when language is changed so UI can update.
    """
    # Signal emitted when language changes - connect UI widgets to refresh
    language_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._current_language = "es"
        self.translations: Dict[str, Dict[str, Any]] = {}
        self._settings_file = os.path.join(os.path.dirname(__file__), 'user_settings.json')
        self.load_translations()
        self._load_saved_language()

    @property
    def current_language(self) -> str:
        return self._current_language

    @current_language.setter
    def current_language(self, value: str):
        if value != self._current_language and value in self.translations:
            self._current_language = value

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

    def _load_saved_language(self):
        """Load saved language preference from settings file"""
        try:
            if os.path.exists(self._settings_file):
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    saved_lang = settings.get('language', 'es')
                    if saved_lang in self.translations:
                        self._current_language = saved_lang
        except Exception:
            pass  # Use default language if loading fails

    def _save_language(self):
        """Save current language to settings file"""
        try:
            settings = {}
            if os.path.exists(self._settings_file):
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

            settings['language'] = self._current_language

            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass  # Silently fail if saving fails

    def set_language(self, language_code: str) -> bool:
        """
        Set current language and emit signal for UI updates.
        Returns True if language was changed successfully.
        """
        if language_code in self.translations:
            old_language = self._current_language
            self._current_language = language_code
            self._save_language()

            if old_language != language_code:
                # Emit signal to notify all connected UI components
                self.language_changed.emit(language_code)
            return True
        return False

    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages"""
        return {
            'es': 'Espanol',
            'en': 'English',
            'de': 'Deutsch'
        }

    def get_language_code_from_name(self, name: str) -> Optional[str]:
        """Get language code from display name"""
        name_to_code = {
            'Espanol': 'es',
            'English': 'en',
            'Deutsch': 'de'
        }
        return name_to_code.get(name)

    def get_language_name_from_code(self, code: str) -> str:
        """Get display name from language code"""
        return self.get_available_languages().get(code, 'Espanol')

    def t(self, key: str, **kwargs) -> str:
        """
        Get translated text for the given key.
        Supports nested keys using dot notation (e.g., 'menu.dashboard').
        No caching - always returns fresh translation for current language.
        """
        # Handle nested keys (e.g., "menu.dashboard")
        keys = key.split('.')
        translation = self.translations.get(self._current_language, {})

        for k in keys:
            if isinstance(translation, dict):
                translation = translation.get(k, None)
            else:
                translation = None
                break

        # Fall back to key itself if translation not found
        if translation is None:
            translation = key

        # Format with kwargs if provided
        if kwargs and isinstance(translation, str):
            try:
                return translation.format(**kwargs)
            except (KeyError, ValueError):
                return translation

        return translation if isinstance(translation, str) else key

    def __call__(self, key: str, **kwargs) -> str:
        """Make the manager callable like t(key)"""
        return self.t(key, **kwargs)


# Global translation manager instance
translator = TranslationManager()


# Convenience function
def t(key: str, **kwargs) -> str:
    """Global translation function"""
    return translator.t(key, **kwargs)