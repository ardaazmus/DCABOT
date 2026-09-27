"use client";

import { useTranslations } from "next-intl";
import { useMemo, useRef, useState } from "react";

import { useExchangeSymbols, useSymbolRules } from "@/lib/api/queries";
import { filterCommands, type CommandItem } from "@/lib/command-filter";
import { cn } from "@/lib/utils";

/**
 * Parite seçici: komut paletindeki Ctrl+K aramasıyla aynı veri ve
 * filtre kullanılır; seçim `symbol-rules` ile doğrulanır.
 */
export function SymbolPicker({
  value,
  onChange,
  error,
}: {
  value: string;
  onChange: (symbol: string) => void;
  error?: string;
}) {
  const t = useTranslations("wizard");
  const [query, setQuery] = useState(value);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const boxRef = useRef<HTMLDivElement>(null);
  const symbols = useExchangeSymbols(open);
  const rules = useSymbolRules(value);

  const items: CommandItem[] = useMemo(
    () =>
      (symbols.data?.symbols ?? []).map((entry) => ({
        id: `symbol:${entry.symbol}`,
        label: entry.symbol,
        hint: entry.status,
      })),
    [symbols.data],
  );
  const results = useMemo(() => filterCommands(items, query, 8), [items, query]);

  function pick(symbol: string) {
    onChange(symbol);
    setQuery(symbol);
    setOpen(false);
  }

  function onInputKey(event: React.KeyboardEvent) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((index) => Math.min(results.length - 1, index + 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((index) => Math.max(0, index - 1));
    } else if (event.key === "Enter") {
      const item = results[active];
      if (item !== undefined) {
        event.preventDefault();
        pick(item.label);
      }
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  const supported = rules.data?.data.bot_supported;
  const reason = rules.data?.data.bot_unsupported_reason;
  const unsupported = value !== "" && supported === false;
  const checking = value !== "" && rules.isPending;
  const reasonText =
    reason === "QUOTE_UNSUPPORTED"
      ? "QUOTE_UNSUPPORTED"
      : reason === "NOT_TRADING"
        ? "NOT_TRADING"
        : reason;

  return (
    <div ref={boxRef} className="relative flex flex-col gap-1.5 text-sm">
      <label htmlFor="wizard-symbol" className="font-medium">
        {t("symbolLabel")}
      </label>
      <input
        id="wizard-symbol"
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls="wizard-symbol-list"
        aria-activedescendant={results[active]?.id}
        aria-invalid={unsupported || error !== undefined || undefined}
        autoComplete="off"
        spellCheck={false}
        placeholder={t("symbolPlaceholder")}
        value={query}
        data-testid="wizard-symbol"
        onChange={(event) => {
          setQuery(event.target.value.toUpperCase());
          setActive(0);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          // Tıklama seçimi tamamlayabilsin diye listeyi geç kapat.
          window.setTimeout(() => setOpen(false), 120);
        }}
        onKeyDown={onInputKey}
        className={cn(
          "rounded-md border bg-background px-3 py-2 font-mono text-sm outline-none",
          "focus-visible:ring-2 focus-visible:ring-ring",
          (unsupported || error !== undefined) && "border-loss",
        )}
      />
      {open && results.length > 0 ? (
        <ol
          id="wizard-symbol-list"
          role="listbox"
          aria-label={t("symbolLabel")}
          className="absolute top-full z-20 mt-1 max-h-64 w-full overflow-y-auto rounded-lg border border-border bg-card p-1"
        >
          {results.map((item, index) => (
            <li
              key={item.id}
              id={item.id}
              role="option"
              aria-selected={index === active}
              onMouseMove={() => setActive(index)}
              onMouseDown={(event) => {
                event.preventDefault();
                pick(item.label);
              }}
              className={cn(
                "flex cursor-pointer items-center justify-between gap-4 rounded-md px-3 py-2 font-mono text-sm",
                index === active && "bg-accent/12",
              )}
            >
              <span>{item.label}</span>
              <span className="text-xs text-muted-foreground">{item.hint}</span>
            </li>
          ))}
        </ol>
      ) : null}
      {checking ? (
        <span role="status" className="text-xs text-muted-foreground">
          {t("symbolLoading")}
        </span>
      ) : null}
      {error !== undefined ? (
        <span role="alert" className="text-xs text-loss">
          {error}
        </span>
      ) : null}
      {/* Gönderim/önizleme hatası aynı metni zaten gösterir; çift uyarı çıkmasın. */}
      {unsupported && error === undefined ? (
        <span role="alert" className="text-xs text-loss" title={reasonText ?? undefined}>
          {t("symbolUnsupported")}
        </span>
      ) : null}
    </div>
  );
}
