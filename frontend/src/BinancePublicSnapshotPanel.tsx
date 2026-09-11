export type BinancePublicSnapshot = {
  environment: "BINANCE_SPOT_TESTNET";
  symbol: string;
  status: string;
  base_asset: string;
  quote_asset: string;
  permissions: string[];
  permission_sets: string[][];
  order_types: string[];
  filters: Array<Record<string, string>>;
  exchange_filters: Array<Record<string, string>>;
  rate_limits: Array<Record<string, string>>;
  response_sha256: string;
  observed_at_us: number;
  read_only: true;
  credential_required: false;
};

type SnapshotStatus = "idle" | "loading" | "ready" | "error";

type BinancePublicSnapshotPanelProps = {
  snapshot: BinancePublicSnapshot | null;
  status: SnapshotStatus;
  error: string;
  onRetry: () => void;
};

const STATUS_META: Record<string, { label: string; description: string; tone: "ok" | "warning" | "neutral" }> = {
  TRADING: { label: "TRADING", description: "Venue bu sembolü trading statüsünde bildiriyor.", tone: "ok" },
  BREAK: { label: "BREAK", description: "Sembol geçici break durumunda.", tone: "warning" },
  HALT: { label: "HALT", description: "Sembol trading için durdurulmuş.", tone: "warning" },
  END_OF_DAY: { label: "END_OF_DAY", description: "Sembol gün-sonu durumunda.", tone: "warning" },
  CANCEL_ONLY: { label: "CANCEL_ONLY", description: "Yeni emir uygun değildir; mevcut emirler için izinler ayrıca değerlendirilir.", tone: "warning" },
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isStringMapArray(value: unknown): value is Array<Record<string, string>> {
  return Array.isArray(value) && value.every((item) => isRecord(item) && Object.values(item).every((value) => typeof value === "string"));
}

export function isBinancePublicSnapshot(value: unknown): value is BinancePublicSnapshot {
  if (!isRecord(value)) return false;
  return value.environment === "BINANCE_SPOT_TESTNET"
    && typeof value.symbol === "string"
    && typeof value.status === "string"
    && typeof value.base_asset === "string"
    && typeof value.quote_asset === "string"
    && isStringArray(value.permissions)
    && Array.isArray(value.permission_sets)
    && value.permission_sets.every(isStringArray)
    && isStringArray(value.order_types)
    && isStringMapArray(value.filters)
    && isStringMapArray(value.exchange_filters)
    && isStringMapArray(value.rate_limits)
    && typeof value.response_sha256 === "string"
    && typeof value.observed_at_us === "number"
    && value.read_only === true
    && value.credential_required === false;
}

function statusMeta(status: string) {
  return STATUS_META[status] ?? { label: `UNKNOWN · ${status}`, description: "Bilinmeyen venue status; bu görünüm emir uygunluğu sonucu üretmez.", tone: "warning" as const };
}

function formatPermissionSets(permissionSets: string[][]): string {
  return permissionSets.length > 0 ? permissionSets.map((set) => `[${set.join(", ")}]`).join(" veya ") : "Belirtilmedi";
}

function JsonDisclosure({ label, value }: { label: string; value: unknown }) {
  return <details className="binance-snapshot-details">
    <summary>{label}</summary>
    <pre>{JSON.stringify(value, null, 2)}</pre>
  </details>;
}

export function BinancePublicSnapshotPanel({ snapshot, status, error, onRetry }: BinancePublicSnapshotPanelProps) {
  const meta = snapshot ? statusMeta(snapshot.status) : null;
  return <section className="panel binance-public-panel" aria-labelledby="binance-public-snapshot-title">
    <div className="panel-heading">
      <div><p className="eyebrow">BINANCE SPOT TESTNET</p><h2 id="binance-public-snapshot-title">Public venue snapshot</h2></div>
      <span className={`binance-snapshot-state ${status}`}>{status === "loading" ? "Okunuyor" : status === "error" ? "FAILED" : snapshot ? "CONNECTED_READ_ONLY" : "Hazır"}</span>
    </div>
    <p className="binance-snapshot-intro">Bu kart yalnız public venue metadata’sını gösterir. Hesap, API anahtarı veya ekonomik sonuç doğrulamaz.</p>
    {status === "loading" && <div className="binance-snapshot-message" role="status" aria-live="polite">Testnet public exchangeInfo okunuyor…</div>}
    {status === "error" && <div className="binance-snapshot-message error" role="alert"><strong>Public snapshot alınamadı.</strong><p>{error}</p><button className="catalog-secondary-button" type="button" onClick={onRetry}>Tekrar dene</button></div>}
    {snapshot && meta && <>
      <div className={`binance-snapshot-status ${meta.tone}`} role="status"><strong>{meta.label}</strong><p>{meta.description}</p></div>
      <dl className="binance-snapshot-facts">
        <div><dt>Sembol</dt><dd><code>{snapshot.symbol}</code></dd></div>
        <div><dt>Base / quote</dt><dd><code>{snapshot.base_asset} / {snapshot.quote_asset}</code></dd></div>
        <div><dt>Ürün izin gereksinimi</dt><dd><code>{formatPermissionSets(snapshot.permission_sets)}</code></dd></div>
        <div><dt>Gözlem zamanı</dt><dd><code>{snapshot.observed_at_us} UTC µs</code></dd></div>
      </dl>
      <div className="binance-snapshot-section">
        <p className="preflight-section-label">VENUE ORDER TYPES</p>
        <div className="binance-order-types" aria-label="Venue order type list">{snapshot.order_types.map((orderType) => <span key={orderType}>{orderType}</span>)}</div>
      </div>
      <div className="binance-snapshot-disclosures">
        <JsonDisclosure label={`Rate limit tanımları · ${snapshot.rate_limits.length}`} value={snapshot.rate_limits} />
        <JsonDisclosure label={`Sembol filtreleri · ${snapshot.filters.length}`} value={snapshot.filters} />
        <JsonDisclosure label={`Exchange filtreleri · ${snapshot.exchange_filters.length}`} value={snapshot.exchange_filters} />
        <JsonDisclosure label="Snapshot hash ve sınırlar" value={{ response_sha256: snapshot.response_sha256, read_only: snapshot.read_only, credential_required: snapshot.credential_required, permissions: snapshot.permissions }} />
      </div>
      <div className="binance-snapshot-boundary" role="note"><strong>Önemli sınır</strong><p>Public metadata, hesap/API anahtarı trade yetkisi, bakiye, emir kabulü veya fill kanıtı değildir. Testnet sanal ortamdır ve state resetlenebilir.</p></div>
    </>}
  </section>;
}
