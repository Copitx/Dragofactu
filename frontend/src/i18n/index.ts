import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import es from "./es.json";
import en from "./en.json";
import de from "./de.json";

const savedLocale = (() => {
  try {
    const stored = localStorage.getItem("dragofactu-ui");
    if (stored) {
      const parsed = JSON.parse(stored) as { state?: { locale?: string } };
      return parsed.state?.locale ?? "es";
    }
  } catch {
    // ignore
  }
  return "es";
})();

i18n.use(initReactI18next).init({
  resources: {
    es: { translation: es },
    en: { translation: en },
    de: { translation: de },
  },
  lng: savedLocale,
  fallbackLng: "es",
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
