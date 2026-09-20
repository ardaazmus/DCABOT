export type BinanceAccountBalance = {
  asset: string;
  free: string;
  locked: string;
};

export type BinanceAccountSnapshot = {
  environment: "BINANCE_SPOT_TESTNET";
  account_type: string;
  can_trade: boolean;
  can_withdraw: boolean;
  can_deposit: boolean;
  permissions: string[];
  update_time_ms: number;
  balances_count: number;
  balances: BinanceAccountBalance[];
  response_sha256: string;
  observed_at_us: number;
  read_only: true;
  credential_required: true;
};

export type BinanceOpenOrder = {
  symbol: string;
  order_id: number;
  client_order_id: string;
  side: string;
  type: string;
  status: string;
  price: string;
  orig_qty: string;
  executed_qty: string;
  time_ms: number;
  update_time_ms: number;
};

export type BinanceOpenOrdersSnapshot = {
  environment: "BINANCE_SPOT_TESTNET";
  orders: BinanceOpenOrder[];
  count: number;
  read_only: true;
  credential_required: true;
};

export type BinanceAccountStatus = "idle" | "loading" | "ready" | "not_configured" | "error";

type BinanceAccountPanelProps = {
  account: BinanceAccountSnapshot | null;
  orders: BinanceOpenOrdersSnapshot | null;
  status: BinanceAccountStatus;
  error: string;
  onRetry: () => void;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isBalanceArray(value: unknown): value is BinanceAccountBalance[] {
  return Array.isArray(value) && value.every((item) => isRecord(item)
    && typeof item.asset === "string"
    && typeof item.free === "string"
    && typeof item.locked === "string");
}

function isOpenOrderArray(value: unknown): value is BinanceOpenOrder[] {
  return Array.isArray(value) && value.every((item) => isRecord(item)
    && typeof item.symbol === "string"
    && typeof item.order_id === "number"
    && typeof item.client_order_id === "string"
    && typeof item.side === "string"
    && typeof item.type === "string"
    && typeof item.status === "string"
    && typeof item.price === "string"
    && typeof item.orig_qty === "string"
    && typeof item.executed_qty === "string"
    && typeof item.time_ms === "number"
    && typeof item.update_time_ms === "number");
}

export function isBinanceAccountSnapshot(value: unknown): value is BinanceAccountSnapshot {
  if (!isRecord(value)) return false;
  return value.environment === "BINANCE_SPOT_TESTNET"
    && typeof value.account_type === "string"
    && typeof value.can_trade === "boolean"
    && typeof value.can_withdraw === "boolean"
    && typeof value.can_deposit === "boolean"
    && isStringArray(value.permissions)
    && typeof value.update_time_ms === "number"
    && typeof value.balances_count === "number"
    && isBalanceArray(value.balances)
    && typeof value.response_sha256 === "string"
    && typeof value.observed_at_us === "number"
    && value.read_only === true
    && value.credential_required === true;
}

export function isBinanceOpenOrdersSnapshot(value: unknown): value is BinanceOpenOrdersSnapshot {
  if (!isRecord(value)) return false;
  return value.environment === "BINANCE_SPOT_TESTNET"
    && isOpenOrderArray(value.orders)
    && typeof value.count === "number"
    && value.read_only === true
    && value.credential_required === true;
}

export function isTestnetCredentialNotConfigured(value: unknown): boolean {
  return isRecord(value) && value.code === "TESTNET_CREDENTIAL_NOT_CONFIGURED";
}

function stateLabel(status: BinanceAccountStatus, hasData: boolean): string {
  if (status === "loading") return "Okunuyor";
  if (status === "error") return "FAILED";
  if (status === "not_configured") return "NOT_CONFIGURED";
  if (hasData) return "CONNECTED_READ_ONLY";
  return "Hazır";
}

function capabilityText(enabled: boolean): string {
  return enabled ? "açık" : "kapalı";
}

function JsonDisclosure({ label, value }: { label: string; value: unknown }) {
  return <details className="binance-snapshot-details">
    <summary>{label}</summary>
    <pre>{JSON.stringify(value, null, 2)}</pre>
  </details>;
}

export function BinanceAccountPanel({ account, orders, status, error, onRetry }: BinanceAccountPanelProps) {
  const hasData = account !== null && orders !== null;
  return <section className="panel binance-public-panel" aria-labelledby="binance-account-title">
    <div className="panel-heading">
      <div><p className="eyebrow">BINANCE SPOT TESTNET</p><h2 id="binance-account-title">Testnet hesap görünümü</h2></div>
      <div className="binance-heading-badges">
        <span className="binance-testnet-badge">TESTNET</span>
        <span className={`binance-snapshot-state ${status}`}>{stateLabel(status, hasData)}</span>
      </div>
    </div>
    <p className="binance-snapshot-intro">Bu kart yalnız testnet hesap bakiyelerini ve açık emirleri gösterir. Salt okunurdur; emir vermez, hesap doğrulamaz.</p>
    {status === "loading" && <div className="binance-snapshot-message" role="status" aria-live="polite">Testnet hesap ve açık emirler okunuyor…</div>}
    {status === "not_configured" && <div className="binance-snapshot-message" role="status"><strong>Testnet hesabı henüz yapılandırılmadı.</strong><p>Backend&apos;de testnet API anahtarı tanımlı değil; bu panel kurulum bekliyor. Anahtar tanımlandıktan sonra tekrar deneyin.</p><button className="catalog-secondary-button" type="button" onClick={onRetry}>Tekrar dene</button></div>}
    {status === "error" && <div className="binance-snapshot-message error" role="alert"><strong>Testnet hesap görünümü alınamadı.</strong><p>{error}</p><button className="catalog-secondary-button" type="button" onClick={onRetry}>Tekrar dene</button></div>}
    {account && orders && <>
      <dl className="binance-snapshot-facts">
        <div><dt>Hesap tipi</dt><dd><code>{account.account_type}</code></dd></div>
        <div><dt>Alım-satım / çekme / yatırma</dt><dd><code>Trade {capabilityText(account.can_trade)} · Çekme {capabilityText(account.can_withdraw)} · Yatırma {capabilityText(account.can_deposit)}</code></dd></div>
        <div><dt>Bakiye</dt><dd><code>{account.balances.length} nonzero · {account.balances_count} toplam</code></dd></div>
        <div><dt>Açık emir</dt><dd><code>{orders.count}</code></dd></div>
      </dl>
      {account.permissions.length > 0 && <div className="binance-snapshot-section">
        <p className="preflight-section-label">HESAP İZİNLERİ</p>
        <div className="binance-order-types" aria-label="Hesap izin listesi">{account.permissions.map((permission) => <span key={permission}>{permission}</span>)}</div>
      </div>}
      <div className="binance-snapshot-section">
        <p className="preflight-section-label">BAKİYELER · {account.balances.length}</p>
        {account.balances.length === 0
          ? <p className="empty-state">Sıfır olmayan bakiye yok.</p>
          : <div className="table-wrap"><table>
            <thead><tr><th>Varlık</th><th>Serbest</th><th>Kilitli</th></tr></thead>
            <tbody>{account.balances.map((balance) => <tr key={balance.asset}><td>{balance.asset}</td><td>{balance.free}</td><td>{balance.locked}</td></tr>)}</tbody>
          </table></div>}
      </div>
      <div className="binance-snapshot-section">
        <p className="preflight-section-label">AÇIK EMİRLER · {orders.count}</p>
        {orders.orders.length === 0
          ? <p className="empty-state">Açık emir yok.</p>
          : <div className="table-wrap"><table>
            <thead><tr><th>Sembol</th><th>Emir ID</th><th>Yön</th><th>Tip</th><th>Durum</th><th>Fiyat</th><th>Miktar</th><th>Gerçekleşen</th></tr></thead>
            <tbody>{orders.orders.map((order) => <tr key={`${order.symbol}-${order.order_id}`}><td>{order.symbol}</td><td>{order.order_id}</td><td>{order.side}</td><td>{order.type}</td><td>{order.status}</td><td>{order.price}</td><td>{order.orig_qty}</td><td>{order.executed_qty}</td></tr>)}</tbody>
          </table></div>}
      </div>
      <div className="binance-snapshot-disclosures">
        <JsonDisclosure label={`Bakiye ham verisi · ${account.balances.length}`} value={account.balances} />
        <JsonDisclosure label={`Açık emir ham verisi · ${orders.orders.length}`} value={orders.orders} />
        <JsonDisclosure label="Snapshot hash ve sınırlar" value={{ response_sha256: account.response_sha256, observed_at_us: account.observed_at_us, update_time_ms: account.update_time_ms, environment: account.environment, read_only: account.read_only, credential_required: account.credential_required, permissions: account.permissions }} />
      </div>
      <div className="binance-snapshot-boundary" role="note"><strong>Önemli sınır</strong><p>Bu ekran salt okunurdur (read_only) ve gerçek emir vermez. Bakiyeler Binance Spot Testnet sanal bakiyesidir; testnet state resetlenebilir. Hesap verisi API anahtarı gerektirir (credential_required).</p></div>
    </>}
  </section>;
}
