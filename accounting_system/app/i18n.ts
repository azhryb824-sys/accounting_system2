import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en/translation.json';
import ar from './locales/ar/translation.json';
import ur from './locales/ur/translation.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ar: { translation: ar },
      ur: { translation: ur },
    },
    fallbackLng: 'ar',
    interpolation: {
      escapeValue: false,
    },
  });

// تغيير اتجاه الصفحة عند تغيير اللغة
i18n.on('languageChanged', (lng) => {
  const dir = lng === 'en' ? 'ltr' : 'rtl';
  document.documentElement.dir = dir;
  document.documentElement.lang = lng;
});

export default i18n;