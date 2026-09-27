import { useEffect, useState } from "react";
import { Badge } from "./Badge";

export type DcaSessionBinding = {
  local_order_id: string;
  role: string;
  venue_order_id: number;
};

export type DcaSessionMode = "TESTNET" | "PAPER";

function isDcaSessionMode(value: unknown): value is DcaSessionMode {
  return value === "TESTNET" || value === "PAPER";
}

export function ModeBadge({ mode }: { mode: DcaSessionMode }) {
  if (mode === "TESTNET") return <span className="binance-testnet-badge">TESTNET</span>;
  return <Badge tone="neutral" label="PAPER" title="Sanal oturum — venue’ye emir gitmez" />;
}

export type DcaSessionRow = {
  session_id: string;
  mode: DcaSessionMode;
  symbol: string;
  average: string;
  qty: string;
  realized_net_after_all_costs: string;
  unrealized: string;
  take_profit_price: string;
  halted: boolean;
  deal_complete: boolean;
  bindings: DcaSessionBinding[];
  starting_balance: string | null;
  virtual_balance: string | null;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isDcaSessionBinding(value: unknown): value is DcaSessionBinding {
  if (!isRecord(value)) return false;
  return typeof value.local_order_id === "string"
    && typeof value.role === "string"
    && typeof value.venue_order_id === "number"
    && Number.isInteger(value.venue_order_id);
}

/* Faz 17 AA.4b: GET .../{id} tam report() çıktısı (gösterilen alanlar;
 * sunucunun fazla alanları guard'dan aynen geçer, UI uydurmaz). */
export type DcaSessionDetail = {
  session_id: string;
  mode: DcaSessionMode;
  symbol: string;
  average: string;
  qty: string;
  cost: string;
  anchor: string;
  take_profit_price: string;
  entry_notional: string;
  realized_gross: string;
  fees: string;
  funding: string;
  realized_net_after_all_costs: string;
  unrealized: string;
  equity: string;
  peak_equity: string;
  max_drawdown: string;
  current_drawdown: string;
  retained_profit_base: string;
  halted: boolean;
  safety_stopped: boolean;
  deal_duration_expired: boolean;
  deal_complete: boolean;
  blockers: string[];
  unsettled_orders: string[];
  last_policy_rejection: string | null;
  bindings: DcaSessionBinding[];
  starting_balance: string | null;
  virtual_balance: string | null;
};

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((entry) => typeof entry === "string");
}

function isDcaSessionDetail(value: unknown): value is DcaSessionDetail {
  if (!isRecord(value)) return false;
  return typeof value.session_id === "string"
    && isDcaSessionMode(value.mode)
    && typeof value.symbol === "string"
    && typeof value.average === "string"
    && typeof value.qty === "string"
    && typeof value.cost === "string"
    && typeof value.anchor === "string"
    && typeof value.take_profit_price === "string"
    && typeof value.entry_notional === "string"
    && typeof value.realized_gross === "string"
    && typeof value.fees === "string"
    && typeof value.funding === "string"
    && typeof value.realized_net_after_all_costs === "string"
    && typeof value.unrealized === "string"
    && typeof value.equity === "string"
    && typeof value.peak_equity === "string"
    && typeof value.max_drawdown === "string"
    && typeof value.current_drawdown === "string"
    && typeof value.retained_profit_base === "string"
    && typeof value.halted === "boolean"
    && typeof value.safety_stopped === "boolean"
    && typeof value.deal_duration_expired === "boolean"
    && typeof value.deal_complete === "boolean"
    && isStringArray(value.blockers)
    && isStringArray(value.unsettled_orders)
    && (typeof value.last_policy_rejection === "string" || value.last_policy_rejection === null)
    && Array.isArray(value.bindings)
    && value.bindings.every(isDcaSessionBinding)
    && (typeof value.starting_balance === "string" || value.starting_balance === null)
    && (typeof value.virtual_balance === "string" || value.virtual_balance === null);
}

export function isDcaSessionDetailResponse(value: unknown): value is { data: DcaSessionDetail } {
  if (!isRecord(value)) return false;
  return isDcaSessionDetail(value.data);
}

/* Faz 17 AA.4b: GET .../{id}/decision — motorun sıradaki önerisi ya da yok.
 * Rol metni aynen gösterilir (BASE/SAFETY:N/EXIT/STOP eşlemesi yapılmaz).
 * limit_price/notional ÖNİZLEMEDİR (null = hesaplanamadı); /place gönderimde
 * kendi hesabını tekrar yapar, tek gerçek kaynak orasıdır. */
export type DcaSessionDecision = {
  role: string;
  qty: string;
  limit_price: string | null;
  notional: string | null;
} | null;

export function isDcaSessionDecisionResponse(value: unknown): value is { data: DcaSessionDecision } {
  if (!isRecord(value)) return false;
  if (value.data === null) return true;
  if (!isRecord(value.data)) return false;
  return typeof value.data.role === "string"
    && typeof value.data.qty === "string"
    && (typeof value.data.limit_price === "string" || value.data.limit_price === null)
    && (typeof value.data.notional === "string" || value.data.notional === null);
}

/* Faz 17 AA.4c: POST .../{id}/place başarı yanıtı (venue kimliği + rapor).
 * Rapor alanları guard'dan aynen geçer, yalnız kimlik doğrulanır. */
export function isDcaSessionPlaceResponse(value: unknown): value is { data: { session_id: string; venue_order_id: number; venue_status: string } } {
  if (!isRecord(value)) return false;
  if (!isRecord(value.data)) return false;
  return typeof value.data.session_id === "string"
    && typeof value.data.venue_order_id === "number"
    && Number.isInteger(value.data.venue_order_id)
    && typeof value.data.venue_status === "string";
}

export function isDcaSessionRow(value: unknown): value is DcaSessionRow {
  if (!isRecord(value)) return false;
  return typeof value.session_id === "string"
    && isDcaSessionMode(value.mode)
    && typeof value.symbol === "string"
    && typeof value.average === "string"
    && typeof value.qty === "string"
    && typeof value.realized_net_after_all_costs === "string"
    && typeof value.unrealized === "string"
    && typeof value.take_profit_price === "string"
    && typeof value.halted === "boolean"
    && typeof value.deal_complete === "boolean"
    && Array.isArray(value.bindings)
    && value.bindings.every(isDcaSessionBinding)
    && (typeof value.starting_balance === "string" || value.starting_balance === null)
    && (typeof value.virtual_balance === "string" || value.virtual_balance === null);
}

export function isDcaSessionCreateResponse(value: unknown): value is { data: { session_id: string } } {
  if (!isRecord(value)) return false;
  return isRecord(value.data) && typeof value.data.session_id === "string";
}

export function isDcaSessionList(value: unknown): value is { data: DcaSessionRow[] } {
  if (!isRecord(value)) return false;
  return Array.isArray(value.data) && value.data.every(isDcaSessionRow);
}

function statusLabel(row: { halted: boolean; deal_complete: boolean }): string {
  if (row.deal_complete) return "Tamamlandı";
  if (row.halted) return "Durduruldu";
  return "Aktif";
}

function boolLabel(value: boolean): string {
  return value ? "Evet" : "Hayır";
}

export type DcaSessionCreateFields = {
  session_id: string;
  symbol: string;
  bot_id: string;
  starting_balance: string;
  mode: DcaSessionMode;
};

type DcaSessionCreateFormProps = {
  defaultSymbol: string;
  baseReady: boolean;
  busy: boolean;
  error: string;
  createdId: string | null;
  onCreate: (fields: DcaSessionCreateFields) => void;
};

/**
 * Faz 17 AA.4-create: yerel DCA oturumu açma formu. Config HER ZAMAN
 * paper.json + studio bindirmesi (App birleştirir); form yalnız kimlik
 * alanları toplar. Oluşturma emir VERMEZ (yerel-kayıt).
 */
export function DcaSessionCreateForm({
  defaultSymbol,
  baseReady,
  busy,
  error,
  createdId,
  onCreate,
}: DcaSessionCreateFormProps) {
  const [sessionId, setSessionId] = useState("");
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [botId, setBotId] = useState("");
  const [startingBalance, setStartingBalance] = useState("");
  const [mode, setMode] = useState<DcaSessionMode>("TESTNET");
  const [formError, setFormError] = useState("");
  const ready = baseReady && !busy;
  function submit() {
    if (sessionId.trim() === "") {
      setFormError("Oturum kimliği boş olamaz.");
      return;
    }
    if (symbol.trim() === "") {
      setFormError("Sembol boş olamaz.");
      return;
    }
    const balance = startingBalance.trim();
    if (balance !== "" && (!/^(?:0|[1-9]\d*)(?:\.\d+)?$/.test(balance) || Number(balance) <= 0)) {
      setFormError("botUSD pozitif exact-ondalık olmalıdır (boş bırakılabilir).");
      return;
    }
    setFormError("");
    onCreate({ session_id: sessionId.trim(), symbol: symbol.trim(), bot_id: botId.trim(), starting_balance: balance, mode });
  }
  return <div className="dca-session-create">
    <p className="eyebrow">YENİ OTURUM · YEREL-KAYIT, EMİR YOK</p>
    {!baseReady && (
      <div className="empty-state" role="status">Taban config bekleniyor — paper.json okununca form açılır.</div>
    )}
    {baseReady && (
      <>
        <label className="field">
          <span className="field-label">Oturum kimliği</span>
          <span className="input-wrap">
            <input aria-label="Oturum kimliği" value={sessionId} onChange={(event) => setSessionId(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Sembol</span>
          <span className="input-wrap">
            <input aria-label="Sembol" value={symbol} onChange={(event) => setSymbol(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Bot kimliği (opsiyonel)</span>
          <span className="input-wrap">
            <input aria-label="Bot kimliği (opsiyonel)" value={botId} onChange={(event) => setBotId(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">botUSD (sanal bakiye, opsiyonel)</span>
          <span className="input-wrap">
            <input aria-label="botUSD (sanal bakiye, opsiyonel)" value={startingBalance} onChange={(event) => setStartingBalance(event.target.value)} placeholder="örn. 10000" />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Oturum modu</span>
          <span className="input-wrap">
            <select aria-label="Oturum modu" value={mode} onChange={(event) => setMode(event.target.value as DcaSessionMode)}>
              <option value="TESTNET">TESTNET (gerçek testnet emri)</option>
              <option value="PAPER">PAPER (sanal dolum, emir yok)</option>
            </select>
          </span>
        </label>
        {formError && <div className="form-error" role="alert">{formError}</div>}
        {error && <div className="form-error" role="alert">{error}</div>}
        {createdId !== null && <div className="venue-selector-message" role="status">Oturum açıldı: {createdId}</div>}
        <button className="secondary-button" type="button" disabled={!ready} onClick={submit}>
          {busy ? "Açılıyor…" : "Oturumu aç"}
        </button>
      </>
    )}
    <p className="helper-text">Config: paper.json + studio bindirmesi (sunucu doğrular). Açılış emir vermez; emir AA.4c-diyaloğuyla ayrı atılır.</p>
  </div>;
}

type DcaSessionsPanelProps = {
  sessions: DcaSessionRow[];
  busy: boolean;
  error: string;
  selectedId?: string | null;
  onRefresh: () => void;
  onSelect?: (sessionId: string) => void;
};

/**
 * Faz 17 AA.4a: testnet DCA oturum listesi (qwen deal-tablosunun GERÇEK
 * karşılığı — `GET /api/testnet/dca-sessions`, exact-Fraction rapor).
 * Faz 17 AA.4b: satır-seçimi detay görünümünü açar (salt-okunur).
 */
export function DcaSessionsPanel({
  sessions,
  busy,
  error,
  selectedId = null,
  onRefresh,
  onSelect,
}: DcaSessionsPanelProps) {
  return <section className="panel dca-sessions-panel" aria-labelledby="dca-sessions-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">TESTNET DCA OTURUMLARI</p>
        <h2 id="dca-sessions-title">Aktif işlemler</h2>
      </div>
      <span className="revision">{sessions.length} oturum</span>
    </div>
    {error && (
      <div className="form-error" role="alert">
        {error}
      </div>
    )}
    <button className="secondary-button" type="button" disabled={busy} onClick={onRefresh}>
      {busy ? "Okunuyor…" : "Oturumları yenile"}
    </button>
    {sessions.length === 0 && !busy && !error && (
      <div className="empty-state" role="status">Kayıtlı DCA oturumu yok. Oturum oluşturma ayrı bir dilimde bağlanacak.</div>
    )}
    {sessions.length > 0 && (
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">Oturum</th>
              <th scope="col">Sembol</th>
              <th scope="col">Mod</th>
              <th scope="col">Durum</th>
              <th scope="col">Ort. Giriş</th>
              <th scope="col">Pozisyon</th>
              <th scope="col">Gerçekleşen Net</th>
              <th scope="col">Gerçekleşmemiş</th>
              <th scope="col">TP Fiyatı</th>
              <th scope="col">Sanal Bakiye</th>
              <th scope="col">Venue Emirleri</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((row) => (
              <tr key={row.session_id}>
                <td title={row.session_id}>
                  {onSelect === undefined ? row.session_id : (
                    <button
                      type="button"
                      className="chip-button"
                      aria-current={selectedId === row.session_id ? "true" : undefined}
                      onClick={() => onSelect(row.session_id)}
                    >
                      {row.session_id}
                    </button>
                  )}
                </td>
                <td>{row.symbol}</td>
                <td><ModeBadge mode={row.mode} /></td>
                <td>{statusLabel(row)}</td>
                <td>{row.average}</td>
                <td>{row.qty}</td>
                <td>{row.realized_net_after_all_costs}</td>
                <td>{row.unrealized}</td>
                <td>{row.take_profit_price}</td>
                <td>{row.virtual_balance ?? "—"}</td>
                <td>{row.bindings.length === 0 ? "—" : row.bindings.length}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )}
    <p className="paper-note">Salt-okunur liste; SO-doluluk sütunu rapor-alanı gelince eklenecek. Satıra tıklayınca detay + motor önerisi açılır; emir yalnız onay-diyaloğuyla (AA.4c) atılır.</p>
  </section>;
}

type DcaSessionDetailPanelProps = {
  sessionId: string;
  detail: DcaSessionDetail | null;
  decision: DcaSessionDecision;
  decisionLoaded: boolean;
  busy: boolean;
  error: string;
  syncBusyRole: string | null;
  syncError: string;
  syncNotice: string;
  placeBusy: boolean;
  placeError: string;
  placeNotice: string;
  paperFillBusy: boolean;
  paperFillError: string;
  paperFillNotice: string;
  onClose: () => void;
  onRefresh: () => void;
  onSync: (role: string) => void;
  onPlace: () => void;
  onPaperFill: () => void;
};

/**
 * Faz 17 AA.4b: tek oturum detayı — tam report() + motor önerisi.
 * Salt-okunur; sync venue'den okur (emir vermez), place onay-diyaloğu açar.
 * Paper-fill ONAYSIZ kardeş-aksiyondur (gerçek para yok) ama PAPER rozetlidir.
 * TÜM sayılar sunucu metni aynen; UI hesap yapmaz, rol eşlemesi yapmaz.
 */
export function DcaSessionDetailPanel({
  sessionId,
  detail,
  decision,
  decisionLoaded,
  busy,
  error,
  syncBusyRole,
  syncError,
  syncNotice,
  placeBusy,
  placeError,
  placeNotice,
  paperFillBusy,
  paperFillError,
  paperFillNotice,
  onClose,
  onRefresh,
  onSync,
  onPlace,
  onPaperFill,
}: DcaSessionDetailPanelProps) {
  const isPaper = detail?.mode === "PAPER";
  const canPlace = decisionLoaded && decision !== null && !placeBusy && !busy && !isPaper;
  const canPaperFill = decisionLoaded && decision !== null && !paperFillBusy && !busy;
  return <section className="panel dca-session-detail-panel" aria-labelledby="dca-session-detail-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">OTURUM DETAYI · SALT-OKUNUR</p>
        <h3 id="dca-session-detail-title">{sessionId}</h3>
      </div>
      <span className="revision">{detail === null ? "—" : detail.symbol}</span>
      {detail !== null && <ModeBadge mode={detail.mode} />}
    </div>
    {error && <div className="form-error" role="alert">{error}</div>}
    <div className="wizard-nav">
      <button className="secondary-button" type="button" disabled={busy} onClick={onRefresh}>
        {busy ? "Okunuyor…" : "Detayı yenile"}
      </button>
      <button className="secondary-button" type="button" onClick={onClose}>Kapat</button>
    </div>
    {renderDetail(detail)}
    <div>
      <p className="eyebrow">MOTOR ÖNERİSİ (SIRADAKİ AKSİYON)</p>
      {!decisionLoaded && <div className="empty-state" role="status">Öneri okunuyor…</div>}
      {decisionLoaded && decision === null && (
        <div className="empty-state" role="status">Motorun sıradaki önerisi yok — gönderilecek emir yok.</div>
      )}
      {decisionLoaded && decision !== null && (
        <dl className="preflight-facts">
          <div><dt>Rol</dt><dd>{decision.role}</dd></div>
          <div><dt>Miktar</dt><dd>{decision.qty}</dd></div>
        </dl>
      )}
    </div>
    {placeError && <div className="form-error" role="alert">{placeError}</div>}
    {placeNotice && <div className="venue-selector-message" role="status">{placeNotice}</div>}
    <p><span className="binance-testnet-badge">TESTNET</span></p>
    <button
      className="primary-button"
      type="button"
      disabled={!canPlace}
      onClick={onPlace}
    >
      {placeBusy ? "Gönderiliyor…" : "Emir gönder (onaylı)"}
    </button>
    <p className="helper-text">{isPaper ? "PAPER oturumda testnet emri verilemez (sunucu 409 ile reddeder) — sanal dolum için Paper Fill kullanın." : "Gerçek testnet emri — düğme yalnız onay-diyaloğu açar, gönderim diyalogdaki ikinci onayla olur."}</p>
    {paperFillError && <div className="form-error" role="alert">{paperFillError}</div>}
    {paperFillNotice && <div className="venue-selector-message" role="status">{paperFillNotice}</div>}
    <p><Badge tone="neutral" label="PAPER" title="Sanal dolum — gerçek emir verilmez, credential gerekmez" /></p>
    <button
      className="secondary-button"
      type="button"
      disabled={!canPaperFill}
      onClick={onPaperFill}
    >
      {paperFillBusy ? "Dolduruluyor…" : "Paper Fill"}
    </button>
    <p className="helper-text">Sanal dolum — motor önerisini aynen işler, onay-diyaloğu yoktur, venue’ye gitmez.</p>
    {syncError && <div className="form-error" role="alert">{syncError}</div>}
    {syncNotice && <div className="venue-selector-message" role="status">{syncNotice}</div>}
    <p className="paper-note">Detay salt-okunur; sync venue'den okur, emir vermez. Mark-girişi bu dilimde yok.</p>
  </section>;

  function renderDetail(current: DcaSessionDetail | null) {
    if (current === null) {
      if (busy) return <div className="empty-state" role="status">Detay okunuyor…</div>;
      return null;
    }
    const rows: Array<[string, string]> = [
      ["Sembol", current.symbol],
      ["Durum", statusLabel(current)],
      ["Ort. giriş", current.average],
      ["Pozisyon", current.qty],
      ["Maliyet", current.cost],
      ["Anchor", current.anchor],
      ["TP fiyatı", current.take_profit_price],
      ["Giriş notional", current.entry_notional],
      ["Gerçekleşen brüt", current.realized_gross],
      ["Komisyon", current.fees],
      ["Fonlama", current.funding],
      ["Gerçekleşen net", current.realized_net_after_all_costs],
      ["Gerçekleşmemiş", current.unrealized],
      ["Özkaynak", current.equity],
      ["Tepe özkaynak", current.peak_equity],
      ["Maks. düşüş", current.max_drawdown],
      ["Anlık düşüş", current.current_drawdown],
      ["Tutulan kâr (baz)", current.retained_profit_base],
      ["Durduruldu", boolLabel(current.halted)],
      ["Safety durdu", boolLabel(current.safety_stopped)],
      ["Süre doldu", boolLabel(current.deal_duration_expired)],
      ["Anlaşma tamam", boolLabel(current.deal_complete)],
      ["Engeller", current.blockers.length === 0 ? "—" : current.blockers.join(", ")],
      ["Bekleyen emirler", current.unsettled_orders.length === 0 ? "—" : current.unsettled_orders.join(", ")],
      ["Son politika reddi", current.last_policy_rejection ?? "—"],
    ];
    if (current.starting_balance !== null) rows.push(["Başlangıç bakiyesi (botUSD)", current.starting_balance]);
    if (current.virtual_balance !== null) rows.push(["Sanal bakiye", current.virtual_balance]);
    return <>
      <dl className="preflight-facts">
        {rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
      </dl>
      <p className="eyebrow">VENUE BAĞLANTILARI</p>
      {current.bindings.length === 0 && (
        <div className="empty-state" role="status">Henüz venue emri yok — sync edilecek bağlantı yok.</div>
      )}
      {current.bindings.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Yerel emir</th>
                <th scope="col">Rol</th>
                <th scope="col">Venue emir</th>
                <th scope="col">Eşitle</th>
              </tr>
            </thead>
            <tbody>
              {current.bindings.map((binding) => (
                <tr key={binding.local_order_id}>
                  <td title={binding.local_order_id}>{binding.local_order_id}</td>
                  <td>{binding.role}</td>
                  <td>{String(binding.venue_order_id)}</td>
                  <td>
                    <button
                      className="secondary-button"
                      type="button"
                      disabled={syncBusyRole !== null || isPaper}
                      title={isPaper ? "PAPER oturumda venue-eşitleme yapılamaz (sunucu 409 ile reddeder)" : undefined}
                      onClick={() => onSync(binding.role)}
                    >
                      {syncBusyRole === binding.role ? "Eşitleniyor…" : "Eşitle"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>;
  }
}

export type DcaPlaceDraft = { role: string; qty: string; limit_price: string | null; notional: string | null };

type DcaPlaceConfirmDialogProps = {
  sessionId: string;
  symbol: string;
  draft: DcaPlaceDraft;
  busy: boolean;
  error: string;
  onConfirm: () => void;
  onCancel: () => void;
};

/**
 * Faz 17 AA.4c: place onay-diyaloğu — dördüncü savunma katmanı (UI).
 * - Gösterilen (rol, miktar, fiyat, notional) HER ZAMAN motor önerisinin
 *   dondurulmuş kopyası; serbest metin girişi, otomatik doldurma,
 *   "hatırla" YOK (bu diyalogda <input> yoktur).
 * - Fiyat/notional ÖNİZLEMEDİR; /place gönderimde tekrar hesaplar. null ise
 *   "sunucu hesaplar" metni aynen durur; UI uydurmaz.
 * - confirmed:true yalnız onConfirm yolundan (bu diyalogdaki düğme) çıkar.
 */
export function DcaPlaceConfirmDialog({
  sessionId,
  symbol,
  draft,
  busy,
  error,
  onConfirm,
  onCancel,
}: DcaPlaceConfirmDialogProps) {
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onCancel();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel]);
  return (
    <div className="confirm-overlay">
      <div className="confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="dca-place-title" aria-describedby="dca-place-summary">
        <h2 id="dca-place-title">Testnet emrini onayla</h2>
        <p><span className="binance-testnet-badge">TESTNET</span></p>
        <p id="dca-place-summary">Bu işlem Binance Spot Testnet&apos;e GERÇEK bir emir gönderir. Onay yalnız bu diyalogdaki düğmeyle verilir.</p>
        <dl className="preflight-facts">
          <div><dt>Oturum</dt><dd>{sessionId}</dd></div>
          <div><dt>Sembol</dt><dd>{symbol}</dd></div>
          <div><dt>Rol</dt><dd>{draft.role}</dd></div>
          <div><dt>Miktar</dt><dd>{draft.qty}</dd></div>
          <div><dt>Limit fiyat (önizleme)</dt><dd>{draft.limit_price ?? "Gönderim-anında sunucu hesaplar (BASE: mark, SAFETY: plan seviyesi, TP: hedef). Bu ekranda gösterilemez; uydurma değer yazılmadı."}</dd></div>
          <div><dt>Notional (önizleme)</dt><dd>{draft.notional ?? "Sunucu hesaplar — UI finansal hesap yapmaz."}</dd></div>
        </dl>
        {error && <div className="form-error" role="alert">{error}</div>}
        <div className="wizard-nav">
          <button type="button" className="secondary-button" disabled={busy} onClick={onCancel} autoFocus>Vazgeç</button>
          <button type="button" className="primary-button" disabled={busy} onClick={onConfirm}>
            {busy ? "Gönderiliyor…" : "Onayla ve gönder"}
          </button>
        </div>
      </div>
    </div>
  );
}
