import type { AppSectionId } from "./appSections";

/**
 * Faz AB.1: hash rota altyapısı. Derin bağlar yalnız bot/deal detayı içindir
 * (`#/bots/<id>`, `#/deals/<id>`); diğer her şey bölüm köküdür. Bilinmeyen
 * ya da bozuk hash Genel Bakış'a düşer. Eski yalın hash'ler (`#bots`, `#lab`)
 * geriye uyumlu okunur.
 */
export type HashRoute = {
  section: AppSectionId;
  detail: { kind: "bot" | "deal"; id: string } | null;
};

const SECTIONS: readonly AppSectionId[] = [
  "overview",
  "bots",
  "create",
  "deals",
  "backtest",
  "lab",
  "risk",
  "market",
  "system",
];

function isSection(value: string): value is AppSectionId {
  return (SECTIONS as readonly string[]).includes(value);
}

export function parseHashRoute(hash: string): HashRoute {
  const clean = hash.startsWith("#") ? hash.slice(1) : hash;
  const path = clean.startsWith("/") ? clean.slice(1) : clean;
  const [head = "", tail = ""] = path.split("/");
  const section: AppSectionId = isSection(head) ? head : "overview";
  if ((section === "bots" || section === "deals") && tail !== "") {
    try {
      const id = decodeURIComponent(tail);
      if (id !== "") return { section, detail: { kind: section === "bots" ? "bot" : "deal", id } };
    } catch {
      /* Bozuk yüzde-kaçıç → düz bölüme düş. */
    }
  }
  return { section, detail: null };
}

export function buildSectionHash(section: AppSectionId): string {
  return `#/${section}`;
}

export function buildDetailHash(kind: "bot" | "deal", id: string): string {
  return `#/${kind === "bot" ? "bots" : "deals"}/${encodeURIComponent(id)}`;
}
