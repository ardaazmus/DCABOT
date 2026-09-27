/* Faz 17 AA.8b: modül-kayıt-defteri salt-okunur liste (qwen sec-core
 * "Modül-Kayıt-Defteri"nin GERÇEK karşılığı — `GET /api/indicators/registry`,
 * `indicator_registry.py` G.4'ün aynısı). Hesap yok, yalnız dizim. */

export type IndicatorRegistryView = {
  indicators: string[];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isIndicatorRegistryResponse(value: unknown): value is { data: IndicatorRegistryView } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return Array.isArray(data.indicators) && data.indicators.every((name) => typeof name === "string");
}

type IndicatorRegistryPanelProps = {
  names: string[];
  busy: boolean;
  error: string;
  onRefresh: () => void;
};

export function IndicatorRegistryPanel({ names, busy, error, onRefresh }: IndicatorRegistryPanelProps) {
  return <section className="panel registry-panel" aria-labelledby="registry-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">ÇEKİRDEK · KAYIT DEFTERİ</p>
        <h2 id="registry-title">Modül kayıt defteri</h2>
      </div>
      <span className="revision">{busy ? "okunuyor" : `${names.length} kayıt`}</span>
    </div>
    {error && <div className="form-error" role="alert">{error}</div>}
    {names.length === 0 && !busy && error === "" && <div className="empty-state">Kayıt defteri boş döndü.</div>}
    {names.length > 0 && (
      <ul className="registry-list">
        {names.map((name) => <li key={name}><code>{name}</code></li>)}
      </ul>
    )}
    <button className="primary-button" type="button" disabled={busy} onClick={onRefresh}>
      {busy ? "Okunuyor…" : "Yenile"}
    </button>
    <p className="paper-note">Sunucudaki indikatör kayıt-defterinin salt-okunur görünümü; `/api/indicators/*` uçları aynı listeye dağıtım yapar.</p>
  </section>;
}
