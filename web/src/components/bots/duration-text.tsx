"use client";

import { useTranslations } from "next-intl";

import { durationParts } from "@/lib/format-time";

/** Mikrosaniye süre → "3 sa 12 dk" (yerel birimle). */
export function DurationText({ timeUs }: { timeUs: number | null }) {
  const t = useTranslations("bots");
  if (timeUs === null) return <span>—</span>;
  const { hours, minutes, seconds } = durationParts(timeUs);
  if (hours > 0) return <span>{t("durationHm", { h: hours, m: minutes })}</span>;
  if (minutes > 0) return <span>{t("durationM", { m: minutes })}</span>;
  return <span>{t("durationS", { s: seconds })}</span>;
}
