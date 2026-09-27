"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";

import { useSymbolRules } from "@/lib/api/queries";

/**
 * "Bu paritede bot kur" düğmesi. Tek kural kaynağı backend'dir
 * (`data.bot_supported` / `data.bot_unsupported_reason`); istemci
 * USDT kontrolü yapmaz.
 */
export function BotSetupButton({ symbol }: { symbol: string }) {
  const t = useTranslations("symbol");
  const rules = useSymbolRules(symbol);

  if (rules.isPending) {
    return (
      <button
        type="button"
        disabled
        aria-label={t("setupBot")}
        className="cursor-wait rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground opacity-60"
      >
        …
      </button>
    );
  }

  const data = rules.data?.data;
  if (data !== undefined && data.bot_supported) {
    return (
      <Link
        href={`/bots/new?symbol=${encodeURIComponent(symbol)}`}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90"
      >
        {t("setupBot")}
      </Link>
    );
  }

  const reason = data?.bot_unsupported_reason;
  const hint =
    reason === "QUOTE_UNSUPPORTED"
      ? t("setupBotDisabledHint")
      : reason === "NOT_TRADING"
        ? t("setupBotNotTradingHint")
        : (reason ?? t("setupBotUnknownHint"));
  return (
    <button
      type="button"
      disabled
      title={hint}
      className="cursor-not-allowed rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground opacity-50"
    >
      {t("setupBot")}
    </button>
  );
}
