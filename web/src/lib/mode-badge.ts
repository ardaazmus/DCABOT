import type { StatusBadgeVariant } from "@/components/status-badge";

export type ModeBadge = { label: string; variant: StatusBadgeVariant };

/**
 * `/api/capabilities` yanıtındaki `execution_mode` alanını rozete çevirir.
 * Bilinen tek değer SIMULATED'dır; uydurma eşleme yok — bilinmeyen değer
 * olduğu gibi gösterilir ve `warn` rozeti alır.
 */
export function modeBadge(executionMode: string): ModeBadge {
  if (executionMode === "SIMULATED") {
    return { label: "Paper", variant: "paper" };
  }
  return { label: executionMode, variant: "warn" };
}
