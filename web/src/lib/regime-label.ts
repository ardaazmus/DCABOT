export type RegimeLabelKey =
  | "regimeTrendUp"
  | "regimeTrendDown"
  | "regimeTrend"
  | "regimeRange"
  | "regimeCompression"
  | "regimeTransition"
  | "regimeUnknown";

/**
 * Backend rejim durumu + yönünü düz dil etiketine çevirir.
 * Bilinmeyen durum olduğu gibi taşınır (`null` anahtar).
 */
export function regimeLabel(
  state: string,
  direction: string | null,
): { key: RegimeLabelKey; raw: null } | { key: null; raw: string } {
  switch (state) {
    case "TREND_CANDIDATE":
      if (direction === "UP") return { key: "regimeTrendUp", raw: null };
      if (direction === "DOWN") return { key: "regimeTrendDown", raw: null };
      return { key: "regimeTrend", raw: null };
    case "RANGE_CANDIDATE":
      return { key: "regimeRange", raw: null };
    case "COMPRESSION":
      return { key: "regimeCompression", raw: null };
    case "TRANSITION":
      return { key: "regimeTransition", raw: null };
    case "UNKNOWN":
      return { key: "regimeUnknown", raw: null };
    default:
      return { key: null, raw: state };
  }
}
