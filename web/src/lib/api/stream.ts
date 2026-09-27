import { landmarkSchema, type Landmark } from "./schemas";

/**
 * SSE `landmark` olayının `data` yükünü doğrular. Bozuk yük hata
 * fırlatır; arayan yakalar ve akışı sürdürür.
 */
export function parseLandmarkEvent(data: string): Landmark {
  return landmarkSchema.parse(JSON.parse(data) as unknown);
}

const BOT_KEYS = [
  ["v2-bots"],
  ["v2-bot"],
  ["v2-bot-stats"],
  ["v2-bot-deals"],
  ["v2-bot-events"],
  ["v2-portfolio"],
  ["events"],
] as const;

const GRID_KEYS = [["v2-grid-state"], ["v2-bot"], ["v2-bot-events"], ["events"]] as const;

const DEAL_KEYS = [
  ["v2-deals"],
  ["v2-deal"],
  ["v2-bot"],
  ["v2-bot-stats"],
  ["v2-bot-deals"],
  ["v2-portfolio"],
  ["events"],
] as const;

/**
 * Landmark türüne göre tazelenmesi gereken sorgu anahtar önekleri.
 * Tanınmayan türler yalnız olay listesini tazeler (ileriye uyumlu).
 */
export function invalidationKeysFor(kind: string): readonly (readonly string[])[] {
  if (kind.startsWith("BOT_")) {
    return BOT_KEYS;
  }
  if (kind.startsWith("GRID_")) {
    return GRID_KEYS;
  }
  if (kind.startsWith("DEAL_") || kind === "SAFETY_ORDER_FILLED") {
    return DEAL_KEYS;
  }
  return [["events"]];
}
