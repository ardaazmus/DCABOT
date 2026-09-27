import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import stringsXml from "./locales/strings.xml?raw";

export type Language = "tr" | "en";

export const LANGUAGE_STORAGE_KEY = "dcabot-lang";

export type StringsTable = Record<string, Partial<Record<Language, string>>>;

function isLanguage(value: unknown): value is Language {
  return value === "tr" || value === "en";
}

/**
 * Faz 12.5: tek-XML i18n. `strings.xml` Vite `?raw` ile gömülür, tarayıcının
 * yerleşik DOMParser'ı ile `{anahtar: {tr, en}}` tablosuna çevrilir.
 * Ek kütüphane yok; sunucuya dil tercihi gitmez (salt görüntü tercihi).
 */
export function parseStringsXml(xml: string): StringsTable {
  const table: StringsTable = {};
  if (typeof xml !== "string" || xml.trim() === "") return table;
  let doc: Document;
  try {
    doc = new DOMParser().parseFromString(xml, "application/xml");
  } catch {
    return table;
  }
  if (doc.querySelector("parsererror")) return table;
  for (const node of Array.from(doc.querySelectorAll("string"))) {
    const key = node.getAttribute("key");
    if (!key) continue;
    const entry: Partial<Record<Language, string>> = {};
    for (const lang of ["tr", "en"] as const) {
      const child = Array.from(node.childNodes).find(
        (candidate) => candidate.nodeType === 1 && (candidate as Element).tagName === lang,
      ) as Element | undefined;
      const text = child?.textContent?.trim() ?? "";
      if (text !== "") entry[lang] = text;
    }
    if (entry.tr !== undefined || entry.en !== undefined) table[key] = entry;
  }
  return table;
}

const DEFAULT_TABLE: StringsTable = parseStringsXml(stringsXml);

export type I18nContextValue = {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string) => string;
};

function translate(table: StringsTable, lang: Language, key: string): string {
  const entry = table[key];
  if (!entry) return key;
  return entry[lang] ?? entry.tr ?? key;
}

const I18nContext = createContext<I18nContextValue>({
  lang: "tr",
  setLang: () => {},
  t: (key: string) => translate(DEFAULT_TABLE, "tr", key),
});

function storedLanguage(): Language {
  try {
    const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (isLanguage(stored)) return stored;
  } catch {
    /* private mode: fall through to default */
  }
  return "tr";
}

export function I18nProvider({
  children,
  strings = stringsXml,
}: {
  children: ReactNode;
  strings?: string;
}) {
  const table = useMemo(() => parseStringsXml(strings), [strings]);
  const [lang, setLangState] = useState<Language>(storedLanguage);

  function setLang(next: Language): void {
    setLangState(next);
    try {
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, next);
    } catch {
      /* private mode: choice still applies for this session */
    }
  }

  const value = useMemo<I18nContextValue>(
    () => ({ lang, setLang, t: (key: string) => translate(table, lang, key) }),
    [table, lang],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  return useContext(I18nContext);
}
