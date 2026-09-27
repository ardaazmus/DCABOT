"use client";

import { useCapabilities } from "@/lib/api/queries";
import { modeBadge } from "@/lib/mode-badge";
import { StatusBadge } from "@/components/status-badge";

/** Üst çubuk mod rozeti; hiçbir zaman gizlenmez. */
export function ModeBadge() {
  const capabilities = useCapabilities();
  if (capabilities.isPending) {
    return <StatusBadge variant="stopped">…</StatusBadge>;
  }
  if (capabilities.isError || capabilities.data === undefined) {
    return <StatusBadge variant="warn">?</StatusBadge>;
  }
  const badge = modeBadge(capabilities.data.execution_mode);
  return <StatusBadge variant={badge.variant}>{badge.label}</StatusBadge>;
}
