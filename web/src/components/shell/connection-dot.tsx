"use client";

import { useTranslations } from "next-intl";

import { useHealth } from "@/lib/api/queries";
import { useStreamStatus } from "@/lib/api/useEventStream";
import { cn } from "@/lib/utils";

/**
 * Bağlantı noktası: SSE canlıyken akış durumunu gösterir, yoksa
 * `/api/health` 15 sn yoklamasına düşer.
 */
export function ConnectionDot() {
  const t = useTranslations("topbar");
  const stream = useStreamStatus((state) => state.status);
  const health = useHealth(stream === "live" ? false : 15_000);
  const connected = stream === "live" || (health.data !== undefined && !health.isError);
  return (
    <span
      role="status"
      aria-label={connected ? t("connected") : t("disconnected")}
      title={connected ? t("connected") : t("disconnectedHint")}
      data-stream={stream}
      className={cn(
        "size-2.5 shrink-0 rounded-full",
        connected ? "bg-profit" : "bg-loss",
      )}
    />
  );
}
