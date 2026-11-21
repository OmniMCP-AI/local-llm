export const languages = {
  en: { label: "English", locale: "en-US", currency: "USD" },
  "zh-Hans": { label: "简体中文", locale: "zh-CN", currency: "CNY" },
  "zh-Hant": { label: "繁體中文", locale: "zh-TW", currency: "TWD" },
  es: { label: "Español", locale: "es-MX", currency: "MXN" },
  ja: { label: "日本語", locale: "ja-JP", currency: "JPY" },
  ko: { label: "한국어", locale: "ko-KR", currency: "KRW" },
  de: { label: "Deutsch", locale: "de-DE", currency: "EUR" },
  hi: { label: "हिन्दी", locale: "hi-IN", currency: "INR" },
  fr: { label: "Français", locale: "fr-FR", currency: "EUR" },
  ar: { label: "العربية", locale: "ar-SA", currency: "SAR", direction: "rtl" },
};

// Use browser preferences where an automatic country choice would be ambiguous,
// including Canada, Belgium, Switzerland, Singapore, and Hong Kong.
const countriesByLanguage = {
  en: "AU GB IE NZ US",
  "zh-Hans": "CN",
  "zh-Hant": "TW",
  es: "AR BO CL CO CR CU DO EC ES GT HN MX NI PA PE PR PY SV UY VE",
  ja: "JP",
  ko: "KR",
  de: "AT DE LI",
  hi: "IN",
  fr: "BL FR GF GP MC MF MQ NC PF PM RE WF YT",
  ar: "AE BH DZ EG IQ JO KW LB LY MA MR OM PS QA SA SD SY TN YE",
};
const countryLanguages = Object.fromEntries(
  Object.entries(countriesByLanguage).flatMap(([language, codes]) =>
    codes.split(" ").map((code) => [code, language]),
  ),
);
const supported = (language) => typeof language === "string" && Object.hasOwn(languages, language);

export function languageForCountry(country) {
  return typeof country === "string" ? countryLanguages[country.toUpperCase()] ?? null : null;
}

export function resolveLanguage(preference, edgeLanguage, browserLanguages) {
  if (supported(preference)) return preference;
  if (supported(edgeLanguage)) return edgeLanguage;
  for (const tag of Array.isArray(browserLanguages) ? browserLanguages : []) {
    if (typeof tag !== "string") continue;
    let locale;
    try {
      locale = new Intl.Locale(tag);
    } catch {
      continue;
    }
    const language = locale.language === "zh"
      ? (locale.maximize().script === "Hant" ? "zh-Hant" : "zh-Hans")
      : locale.language;
    if (supported(language)) return language;
  }
  return "en";
}
