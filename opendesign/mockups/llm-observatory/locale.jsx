import React, { createContext, useContext, useEffect, useState } from "react";
import { ChevronDown, Globe2 } from "lucide-react";
import { ConverterFactory } from "opencc-js/core";
import fromSimplified from "opencc-js/from/cn";
import toTaiwan from "opencc-js/to/twp";
import { catalogTranslations, eastAsianGermanCatalogTranslations } from "./catalog-translations";
import { comparisonTranslations, eastAsianGermanComparisonTranslations } from "./comparison-translations";
import { costTranslations, eastAsianGermanCostTranslations } from "./cost-translations";
import { feedbackTranslations, eastAsianGermanFeedbackTranslations } from "./feedback-translations";
import { siteTranslations, eastAsianGermanSiteTranslations } from "./site-translations";
import { languages, resolveLanguage } from "./locale-settings.mjs";
import { FX_DATE, FX_SOURCE, datedDisplayRate, hasReference, rates, supplementalRates } from "./display-fx.mjs";

const translationOrder = ["hi", "es", "ar", "fr"];
const translations = { ...catalogTranslations, ...comparisonTranslations, ...costTranslations, ...feedbackTranslations, ...siteTranslations };
const additionalOrder = ["ja", "ko", "de"];
const additionalTranslations = {
  ...eastAsianGermanCatalogTranslations,
  ...eastAsianGermanComparisonTranslations,
  ...eastAsianGermanCostTranslations,
  ...eastAsianGermanFeedbackTranslations,
  ...eastAsianGermanSiteTranslations,
};
const unsupportedCodedUnits = new Set(["XAG", "XAU", "XBA", "XBB", "XBC", "XBD", "XDR", "XPD", "XPT", "XSU", "XTS", "XUA", "XXX"]);
const browserCodes = Intl.supportedValuesOf?.("currency") ?? [];
const codes = [...new Set([...Object.keys(rates), ...Object.keys(supplementalRates), ...browserCodes])].filter((code) => !unsupportedCodedUnits.has(code)).sort();
const supported = new Set(codes);
const preferenceKey = "fastest-locale-v1";
const LocaleContext = createContext(null);
export const quoteCurrency = (region) => region === "cn" ? "CNY" : "USD";

let toTraditional;
function traditionalCopy(chinese) {
  if (!chinese) return chinese;
  toTraditional ??= ConverterFactory(fromSimplified, toTaiwan, [[
    ["顯卡", "顯示卡"], ["顯存", "顯示記憶體"], ["反饋", "意見回饋"], ["幣種", "幣別"],
  ]]);
  return toTraditional(chinese);
}

function readChoices() {
  try {
    const stored = JSON.parse(localStorage.getItem(preferenceKey));
    if (stored && typeof stored === "object") return stored;
  } catch {}
  return {};
}

export function LocaleProvider({ children }) {
  const [initial] = useState(readChoices);
  const [preference, setLanguage] = useState(Object.hasOwn(languages, initial.language) ? initial.language : null);
  const [choice, setCurrency] = useState(supported.has(initial.currency) ? initial.currency : "auto");
  const [manual, setManual] = useState(initial.manual ?? {});
  const language = resolveLanguage(preference, document.documentElement.dataset.visitorLanguage, navigator.languages?.length ? navigator.languages : [navigator.language]);
  const languageSettings = languages[language];
  const currency = choice === "auto" ? languageSettings.currency : choice;
  const locale = languageSettings.locale;
  const translationIndex = translationOrder.indexOf(language);
  const additionalIndex = additionalOrder.indexOf(language);
  const t = (english, chinese, values) => {
    const translated = language === "zh-Hans" ? chinese
      : language === "zh-Hant" ? traditionalCopy(chinese)
      : additionalIndex >= 0 ? additionalTranslations[english]?.[additionalIndex]
      : translations[english]?.[translationIndex];
    const text = translated || english;
    return values ? text.replace(/\{([\w]+)\}/g, (placeholder, key) => Object.hasOwn(values, key) ? values[key] : placeholder) : text;
  };
  const reference = (code) => {
    const usdRate = supplementalRates[code]?.unitsPerUsd ?? manual[code];
    // Manual and supplemental entries are units per USD. ECB entries are units per EUR.
    return rates[code] ?? (Number.isFinite(usdRate) && usdRate > 0 ? usdRate * rates.USD : null);
  };
  const convertMoney = (value, fromCurrency = "USD", toCurrency = currency) => {
    if (!Number.isFinite(value)) return null;
    if (fromCurrency === toCurrency) return value;
    const fromRate = reference(fromCurrency);
    const toRate = reference(toCurrency);
    return fromRate && toRate ? value / fromRate * toRate : null;
  };
  const formatMoney = (value, sourceCurrency = "USD", options = {}) => {
    if (!Number.isFinite(value)) return "—";
    const converted = convertMoney(value, sourceCurrency);
    const code = converted === null ? sourceCurrency : currency;
    return new Intl.NumberFormat(locale, {
      style: "currency", maximumFractionDigits: 2, ...options, currency: code,
    }).format(converted ?? value);
  };
  const displayCurrency = (source = "USD") => convertMoney(1, source) === null ? source : currency;
  const hasRate = reference(currency) !== null;

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = languageSettings.direction ?? "ltr";
    try { localStorage.setItem(preferenceKey, JSON.stringify({ language: preference, currency: choice, manual })); } catch {}
  }, [language, languageSettings, preference, choice, manual]);

  return <LocaleContext.Provider value={{ language, currency, locale, choice, setLanguage, setCurrency, manual, setManual, t, hasRate, displayCurrency, convertMoney, formatMoney }}>
    {children}
  </LocaleContext.Provider>;
}

export function useLocale() {
  return useContext(LocaleContext);
}

function CurrencyRate({ currency, manual, setManual, t }) {
  const [rate, setRate] = useState(manual[currency] ?? "");
  function save(event) {
    event.preventDefault();
    const next = Number(rate);
    if (Number.isFinite(next) && next > 0) setManual((old) => ({ ...old, [currency]: next }));
  }
  return <form className="locale-rate" onSubmit={save}>
    <label>{t("Units of {currency} per 1 USD", "每 1 美元兑换的 {currency} 数量", { currency })}
      <input type="number" min="0" step="any" required value={rate} onChange={(event) => setRate(event.target.value)} />
    </label>
    <button className="btn outline" type="submit">{t("Apply rate", "应用汇率")}</button>
  </form>;
}

export function LocaleControls({ datedRatesOnly = false, sourceCurrency = "USD" }) {
  const { language, currency, locale, choice, setLanguage, setCurrency, setManual, manual, t, hasRate } = useLocale();
  const names = new Intl.DisplayNames([locale], { type: "currency" });
  const hasDisplayRate = (code) => datedRatesOnly ? Boolean(datedDisplayRate(sourceCurrency, code)) : hasReference(code);
  const option = (code) => <option key={code} value={code}>{code} / {names.of(code)}</option>;
  return <details className="locale-controls">
    <summary aria-label={t("Language and currency", "语言与货币")}><Globe2 size={16} aria-hidden="true" />{languages[language].label}<span dir="ltr">{currency}</span><ChevronDown size={13} aria-hidden="true" /></summary>
    <div className="locale-controls-body">
      <label>{t("Language", "语言")} <select value={language} onChange={(event) => setLanguage(event.target.value)}>
        {Object.entries(languages).map(([tag, { label }]) => <option key={tag} value={tag} lang={tag}>{label}</option>)}
      </select></label>
      <label>{t("Display currency", "显示货币")} <select value={choice} onChange={(event) => setCurrency(event.target.value)}>
        <option value="auto">{t("Follow language", "跟随语言")} ({languages[language].currency})</option>
        <optgroup label={t("Reference rates available", "有参考汇率")}>{codes.filter(hasDisplayRate).map(option)}</optgroup>
        <optgroup label={datedRatesOnly ? t("Display FX unavailable", "缺少显示汇率") : t("Set a custom rate", "可手动设置汇率")}>{codes.filter((code) => !hasDisplayRate(code)).map(option)}</optgroup>
      </select></label>
      {!datedRatesOnly && !hasReference(currency) && <CurrencyRate key={currency} currency={currency} manual={manual} setManual={setManual} t={t} />}
      <p>{t("Market and original quote currency stay the same.", "市场与原始报价币种保持不变。")}</p>
      {!datedRatesOnly && !hasRate && <p role="status">{t("Showing source currencies until a rate is supplied.", "在填写汇率前显示原始报价币种。")}</p>}
    </div>
  </details>;
}

export function LocaleStatus() {
  const { language, currency, t, hasRate } = useLocale();
  const extra = supplementalRates[currency];
  return <div className="locale-status">
    {language !== "en" && <span>{t("Some research and detail pages are in their original language.", "部分研究资料和深层页面保留原文。")}</span>}
    <span>{hasReference(currency) ? t("Display FX when needed", "换算参考汇率") : hasRate ? t("Custom display rate, with reference cross-rates", "自定义显示汇率，使用参考交叉汇率") : t("Display FX unavailable. Showing source currencies.", "缺少显示汇率，暂用原始币种。")}
      {hasRate && <> / <a href={FX_SOURCE} target="_blank" rel="noreferrer" dir="ltr">ECB {FX_DATE}</a></>}
      {extra && <> / <a href={extra.url} target="_blank" rel="noreferrer" dir="ltr">{extra.label}{extra.date && " " + extra.date} ({currency})</a></>}
    </span>
  </div>;
}
