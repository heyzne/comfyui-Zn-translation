/**
 * Zn Translation - 语言映射
 * 仅支持中英互译
 */

export const LOCALES = {
    "zh-CN": {
        "nativeName": "中文",
        "englishName": "Chinese Simplified",
        "flag": "🇨🇳"
    },
    "en-US": {
        "nativeName": "English",
        "englishName": "English",
        "flag": "🇺🇸"
    }
};

export const DEFAULT_LOCALE = "zh-CN";

export const LOCALE_MAP = {
    "zh-CN": "zh",
    "en-US": "en"
};

export function getCurrentLocale() {
    return localStorage.getItem('zn-translation-locale') || DEFAULT_LOCALE;
}

export function setCurrentLocale(locale) {
    if (LOCALES[locale]) {
        localStorage.setItem('zn-translation-locale', locale);
        return true;
    }
    return false;
}

export function getLocaleName(locale, native = true) {
    const loc = LOCALES[locale];
    if (!loc) return locale;
    return native ? loc.nativeName : loc.englishName;
}

export function getAvailableLocales() {
    return Object.entries(LOCALES).map(([code, info]) => ({
        code,
        name: info.nativeName,
        englishName: info.englishName
    }));
}
