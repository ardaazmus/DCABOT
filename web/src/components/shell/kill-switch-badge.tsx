"use client";

import { Power } from "lucide-react";
import { useTranslations } from "next-intl";

import { StatusBadge } from "@/components/status-badge";
import { useCanary } from "@/lib/api/queries";

/**
 * Kill switch salt okunur rozeti (`/api/risk/canary` yanıtındaki
 * `kill_switch_engaged` alanından). Hiçbir genişlikte gizlenmez;
 * dar ekranda yalnız ikon + renk görünür, metin `aria-label`'dedir.
 * Açma/kapama W-F8'de.
 */
export function KillSwitchBadge() {
  const t = useTranslations("topbar");
  const canary = useCanary();
  if (canary.isPending) {
    return (
      <StatusBadge role="img" variant="stopped" aria-label={t("killSwitchUnknown")}>
        <Power className="size-3" aria-hidden="true" />
        <span className="hidden sm:inline">{t("killSwitchUnknown")}</span>
      </StatusBadge>
    );
  }
  if (canary.isError || canary.data === undefined) {
    return (
      <StatusBadge role="img" variant="warn" aria-label={t("killSwitchUnknown")}>
        <Power className="size-3" aria-hidden="true" />
        <span className="hidden sm:inline">{t("killSwitchUnknown")}</span>
      </StatusBadge>
    );
  }
  const engaged = canary.data.data.kill_switch_engaged;
  const label = engaged ? t("killSwitchOn") : t("killSwitchOff");
  return (
    <StatusBadge
      role="img"
      variant={engaged ? "error" : "stopped"}
      title={t("killSwitchHint")}
      aria-label={label}
    >
      <Power className="size-3" aria-hidden="true" />
      <span className="hidden sm:inline">{label}</span>
    </StatusBadge>
  );
}
