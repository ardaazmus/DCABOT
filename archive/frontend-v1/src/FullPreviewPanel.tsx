/* `/api/preview/full` kilitli sözleşmesi (tests/api/test_preview_full.py): seviye
 * satırı {index, price, qty, notional}; previewOverlay.ts ile aynı şekil. */
export type FullPreviewLevel = {
  index: number;
  price: string;
  qty: string;
  notional: string;
};

export type FullPreview = {
  symbol: string;
  anchor: string;
  average_cost: string;
  take_profit_price: string | null;
  stop_loss_price: string | null;
  liquidation_price: null;
  liquidation_note: string;
  estimated_initial_margin: string;
  planned_gross_notional: string;
  within_gross_entry_cap: boolean;
  levels: FullPreviewLevel[];
};

export type FullPreviewStatus = "idle" | "loading" | "ready" | "error";

export type StudioOverrides = {
  safety_qty: string;
  safety_count: string;
  deviation: string;
  leverage: string;
  direction: string;
  margin_mode: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isFullPreviewLevel(value: unknown): value is FullPreviewLevel {
  if (!isRecord(value)) return false;
  return typeof value.index === "number"
    && Number.isInteger(value.index)
    && value.index >= 1
    && typeof value.price === "string"
    && typeof value.qty === "string"
    && typeof value.notional === "string";
}

export function isFullPreview(value: unknown): value is FullPreview {
  if (!isRecord(value)) return false;
  return typeof value.symbol === "string"
    && typeof value.anchor === "string"
    && typeof value.average_cost === "string"
    && (typeof value.take_profit_price === "string" || value.take_profit_price === null)
    && (typeof value.stop_loss_price === "string" || value.stop_loss_price === null)
    && value.liquidation_price === null
    && typeof value.liquidation_note === "string"
    && typeof value.estimated_initial_margin === "string"
    && typeof value.planned_gross_notional === "string"
    && typeof value.within_gross_entry_cap === "boolean"
    && Array.isArray(value.levels)
    && value.levels.every(isFullPreviewLevel);
}

export function isFullPreviewResponse(value: unknown): value is { data: FullPreview } {
  if (!isRecord(value)) return false;
  return isFullPreview(value.data);
}

/**
 * Faz 17 AA.5a: studio-form değerlerini sunucu-taban-config üzerine bindirir.
 * Yalnız alan-kopyalama (safety_count için studio-disipliniyle aynı Number
 * dönüşümü; leverage/direction/margin_mode VERBATIM string — Config bekler);
 * varsayılan UYDURULMAZ, tüm doğrulama `Config.parse` tarafında.
 */
export function mergeConfigOverrides(
  base: Record<string, unknown>,
  overrides: StudioOverrides,
): Record<string, unknown> {
  return {
    ...base,
    safety_qty: overrides.safety_qty,
    safety_count: Number(overrides.safety_count),
    deviation: overrides.deviation,
    leverage: overrides.leverage,
    direction: overrides.direction,
    margin_mode: overrides.margin_mode,
  };
}

const STUDIO_LEVERAGE_PATTERN = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;

/**
 * Futures-paper istemci ön-kontrolü: yalnız format/aralık REHBERİ (görüntü).
 * Nihai doğrulama `Config.parse` tarafındadır (sunucu ≤100 kabul ederken
 * istemci 1-20 önerir — fark metinde açıkça yazılır, sessiz daraltma yok).
 */
export function studioLeverageIssue(value: string): string | undefined {
  const trimmed = value.trim();
  if (!STUDIO_LEVERAGE_PATTERN.test(trimmed)) return "Kaldıraç exact-ondalık olmalıdır.";
  const numeric = Number(trimmed);
  if (!(numeric >= 1 && numeric <= 20)) return "Kaldıraç 1-20 aralığında olmalıdır (sunucu ≤100 kabul eder).";
  return undefined;
}

/** Kaldıraçlı/futures-tarzı uyarı-notu koşulu (görüntü-disiplini, hesap yok). */
export function isFuturesStyleConfig(config: { leverage: string; direction: string }): boolean {
  if (config.direction === "SHORT") return true;
  const trimmed = config.leverage.trim();
  return STUDIO_LEVERAGE_PATTERN.test(trimmed) && Number(trimmed) > 1;
}

type FullPreviewPanelProps = {
  preview: FullPreview | null;
  status: FullPreviewStatus;
  error: string;
  baseReady: boolean;
  launchBusy: boolean;
  launchError: string;
  launchedId: string | null;
  onLaunchPaper: () => void;
};

export function FullPreviewPanel({
  preview,
  status,
  error,
  baseReady,
  launchBusy,
  launchError,
  launchedId,
  onLaunchPaper,
}: FullPreviewPanelProps) {
  const launchReady = baseReady && status === "ready" && preview !== null && !launchBusy;
  return <section className="panel full-preview-panel" aria-labelledby="full-preview-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">TAM ÖNİZLEME · PAPER TABANLI</p>
        <h2 id="full-preview-title">Seviye önizlemesi</h2>
      </div>
      {status === "ready" && preview !== null ? (
        <span className="state-label ready">Hesaplandı</span>
      ) : status === "loading" ? (
        <span className="state-label pending">Hesaplanıyor</span>
      ) : status === "error" ? (
        <span className="state-label error">Hata</span>
      ) : (
        <span className="state-label">Hazır değil</span>
      )}
    </div>
    {!baseReady && (
      <div className="empty-state" role="status">Taban config bekleniyor — paper.json okununca önizleme otomatik hesaplanır.</div>
    )}
    {baseReady && status === "loading" && preview === null && (
      <div className="venue-selector-message" role="status">Seviyeler hesaplanıyor…</div>
    )}
    {baseReady && status === "error" && (
      <div className="venue-selector-message error" role="alert">
        <strong>Seviye önizlemesi hesaplanamadı.</strong>
        <p>{error}</p>
      </div>
    )}
    {preview !== null && (
      <>
        <dl className="dataset-facts">
          <div><dt>Ortalama maliyet</dt><dd>{preview.average_cost}</dd></div>
          <div><dt>TP fiyatı</dt><dd>{preview.take_profit_price ?? "—"}</dd></div>
          <div><dt>SL fiyatı</dt><dd>{preview.stop_loss_price ?? "—"}</dd></div>
          <div><dt>Tahmini başlangıç marjı</dt><dd>{preview.estimated_initial_margin}</dd></div>
          <div><dt>Likidasyon</dt><dd>{preview.liquidation_note}</dd></div>
        </dl>
        {preview.levels.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">SO#index</th>
                  <th scope="col">Fiyat</th>
                  <th scope="col">Miktar</th>
                  <th scope="col">Notional</th>
                </tr>
              </thead>
              <tbody>
                {preview.levels.map((level) => (
                  <tr key={`so-${level.index}`}>
                    <td>SO#{level.index}</td>
                    <td>{level.price}</td>
                    <td>{level.qty}</td>
                    <td>{level.notional}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </>
    )}
    <p className="helper-text">paper.json tabanı + studio-form bindirmesi; tüm hesap sunucuda (exact). Girdi-kapısı: anchor + 3 studio-alanı.</p>
    {launchError && <div className="form-error" role="alert">{launchError}</div>}
    {launchedId !== null && <div className="venue-selector-message" role="status">Paper oturum açıldı: {launchedId} — DCA listesi güncellendi.</div>}
    <button className="primary-button" type="button" disabled={!launchReady} onClick={onLaunchPaper}>
      {launchBusy ? "Açılıyor…" : "Paper'da Başlat"}
    </button>
    <p className="helper-text">Stüdyo config'i aynen paper-oturuma açılır (mode: PAPER, emir yok); kimlik otomatik üretilir, sunucu doğrular.</p>
  </section>;
}
