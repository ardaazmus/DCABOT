"use client";

import { useTranslations } from "next-intl";

import { EmptyState } from "@/components/empty-state";

/** Kabuk sayfaları için dürüst yer tutucu: sahte veri yok. */
export function ComingSoon({
  title,
  hintKey,
  actionLabel,
  actionHref,
}: {
  title: string;
  hintKey: "dashboardHint" | "botsHint" | "dealsHint" | "backtestHint" | "marketHint" | "marketDetailHint";
  actionLabel?: string;
  actionHref?: string;
}) {
  const t = useTranslations("pages");
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-2">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <EmptyState
        title={t("comingTitle")}
        description={t(hintKey)}
        actionLabel={actionLabel}
        actionHref={actionHref}
      />
    </div>
  );
}
