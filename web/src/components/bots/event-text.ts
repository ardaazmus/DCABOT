import type { BotEvent } from "@/lib/api/schemas";

export type EventTone = "open" | "fill" | "close" | "note";

const KIND_TEXT: Record<string, { key: string; tone: EventTone }> = {
  DEAL_STARTED: { key: "eventDealStarted", tone: "open" },
  SAFETY_ORDER_FILLED: { key: "eventSafetyFilled", tone: "fill" },
  MANUAL_ORDER_FILLED: { key: "eventManualFilled", tone: "fill" },
  DEAL_CLOSED: { key: "eventDealClosed", tone: "close" },
  AMBIGUOUS_BAR_SAFETY_FIRST: { key: "eventAmbiguous", tone: "note" },
  NOTE: { key: "eventNote", tone: "note" },
};

/** Kapanış nedeni → rozet/metin anahtarı (ham kod arayüzde görünmez). */
export const CLOSE_REASON_KEY: Record<string, string> = {
  TAKE_PROFIT: "closeTakeProfit",
  STOP_LOSS: "closeStopLoss",
  MANUAL_CLOSE: "closeManual",
  CANCELLED: "closeCancelled",
};

/**
 * Olay türü → i18n anahtarı + görsel ton. Bilinmeyen tür ham
 * gösterilir (eventUnknown), akış düşmez.
 */
export function describeBotEvent(event: BotEvent): { key: string; tone: EventTone } {
  return KIND_TEXT[event.kind] ?? { key: "eventUnknown", tone: "note" };
}

/** Detay anahtarları düz metin çiplere dönüşür (null → "—"). */
export function detailChips(detail: Record<string, string | number | null>): {
  label: string;
  value: string;
}[] {
  return Object.entries(detail).map(([label, value]) => ({
    label,
    value: value === null ? "—" : String(value),
  }));
}
