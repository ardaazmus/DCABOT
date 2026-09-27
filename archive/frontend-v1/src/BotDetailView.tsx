import type { ReactNode } from "react";

import type { BotDcaPerformanceView, BotProfileView } from "./BotPanel";
import { readDraftBotType } from "./BotTable";
import type { WizardPreviewParams } from "./BotWizard";
import { LiquidationStatusSection, type LiquidationStatusView } from "./LiquidationStatusSection";

/**
 * Faz 17 A.4: tam sayfa bot detay (qwen `sec-botdetail`) — popup YOK, yalnız
 * görünüm-durumu ile gezinme. Gösterilen her değer gerçektir: profil+sessions
 * backend'den, tip+taslak istemci taslağından (etiketli), grafik+overlay A.3
 * deseniyle. Faz 17 AA.3a: DCA-performans kutusu testnet-okuma uçlarından
 * (deal-count + performance). Bilinçli eksikler (backend karşılığı yok,
 * uydurulmadı): açma/kapama anahtarı, sparkline, tam strateji-ayarları.
 */
export function BotDetailView({
  botId,
  profile,
  botIds,
  sessionCount,
  draftParams,
  loading,
  renderChart,
  overlayNote,
  liquidation,
  liquidationBusy,
  liquidationError,
  onRefreshLiquidation,
  dcaPerformance,
  dcaActiveDeals,
  dcaBusy,
  dcaError,
  onRefreshDca,
  onBack,
  onSelectBot,
}: {
  botId: string;
  profile: BotProfileView | null;
  botIds: string[];
  sessionCount: number;
  draftParams: WizardPreviewParams | null;
  loading: boolean;
  renderChart: () => ReactNode;
  overlayNote?: string | null;
  liquidation: LiquidationStatusView | null;
  liquidationBusy: boolean;
  liquidationError: string;
  onRefreshLiquidation: () => void;
  dcaPerformance: BotDcaPerformanceView | null;
  dcaActiveDeals: number | null;
  dcaBusy: boolean;
  dcaError: string;
  onRefreshDca: () => void;
  onBack: () => void;
  onSelectBot: (botId: string) => void;
}) {
  const loaded = profile !== null && profile.bot_id === botId;
  const botType = readDraftBotType(botId);
  return (
    <section className="bot-create-view" aria-labelledby="bot-detail-title">
      <div className="bot-create-head">
        <button className="secondary-button" type="button" onClick={onBack}>
          ← Botlar
        </button>
        <h2 id="bot-detail-title">{loaded ? `${profile.bot_id} · ${profile.name}` : botId}</h2>
        {botType && <span className="state-label">{botType}</span>}
        {loaded && <span className="state-label">{profile.pairs.length} pair</span>}
        {loaded && <span className="state-label">{sessionCount} session</span>}
      </div>
      {botIds.length > 0 && (
        <div className="panel">
          <p className="eyebrow">DİĞER BOTLAR · hızlı geçiş</p>
          <div className="chipbar" role="group" aria-label="Diğer botlar">
            {botIds.map((id) => (
              <button
                key={id}
                type="button"
                className="chip-button"
                aria-pressed={id === botId}
                disabled={loading || id === botId}
                onClick={() => onSelectBot(id)}
              >
                {id}
              </button>
            ))}
          </div>
        </div>
      )}
      {loaded ? (
        <dl className="binance-snapshot-facts">
          <div><dt>Pair</dt><dd>{profile.pairs.length}</dd></div>
          <div><dt>Session</dt><dd>{sessionCount}</dd></div>
          <div><dt>Bütçe</dt><dd>{profile.virtual_quote_budget} USDT</dd></div>
          <div><dt>Blacklist</dt><dd>{profile.blacklist.length}</dd></div>
          <div><dt>Favori</dt><dd>{profile.favorites.length}</dd></div>
          <div><dt>Tip</dt><dd>{botType ?? "—"}</dd></div>
        </dl>
      ) : (
        <p className="helper-text" role="status">{loading ? "Bot yükleniyor…" : "Bot profili alınamadı."}</p>
      )}
      {loaded && (
        <section className="panel" aria-labelledby="bot-detail-dca-title">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">DCA PERFORMANSI · TESTNET</p>
              <h2 id="bot-detail-dca-title">Oturum toplamları</h2>
            </div>
            <button className="secondary-button" type="button" disabled={dcaBusy} aria-label="DCA toplamlarını yenile" onClick={onRefreshDca}>
              {dcaBusy ? "Okunuyor…" : "Yenile"}
            </button>
          </div>
          {dcaError && <div className="form-error" role="alert">{dcaError}</div>}
          {dcaPerformance === null && !dcaBusy && !dcaError && (
            <p className="helper-text" role="status">Bu botun DCA-oturum toplamı okunamadı — oturum-açılışında bot-bağlantısı kurulmamış olabilir.</p>
          )}
          {dcaPerformance !== null && (
            <dl className="binance-snapshot-facts">
              <div><dt>Aktif deal</dt><dd>{dcaActiveDeals === null ? "—" : dcaActiveDeals}</dd></div>
              <div><dt>Toplam deal</dt><dd>{dcaPerformance.deal_count}</dd></div>
              <div><dt>Tamamlanan</dt><dd>{dcaPerformance.completed_deal_count}</dd></div>
              <div><dt>Kazanan</dt><dd>{dcaPerformance.win_count}</dd></div>
              <div><dt>Win rate</dt><dd>{dcaPerformance.win_rate ?? "—"}</dd></div>
              <div><dt>Toplam net</dt><dd>{dcaPerformance.total_realized_net}</dd></div>
              <div><dt>Maks. düşüş</dt><dd>{dcaPerformance.max_drawdown}</dd></div>
            </dl>
          )}
          <p className="helper-text">Testnet DCA-oturumlarından exact-Fraction toplam; “—” = tamamlanan deal yok (oran tanımsız).</p>
        </section>
      )}
      <div className="bot-create-chart">
        {renderChart()}
        {overlayNote ? <p className="helper-text" role="status">{overlayNote}</p> : null}
      </div>
      {loaded && (
        <section className="panel" aria-labelledby="bot-detail-settings-title">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">AYARLAR</p>
              <h2 id="bot-detail-settings-title">Aktif ayarlar</h2>
            </div>
          </div>
          <dl className="dataset-facts">
            <div><dt>Pairler</dt><dd>{profile.pairs.join(", ") || "—"}</dd></div>
            <div><dt>Blacklist</dt><dd>{profile.blacklist.join(", ") || "—"}</dd></div>
            <div><dt>Favoriler</dt><dd>{profile.favorites.join(", ") || "—"}</dd></div>
            <div>
              <dt>Güvenlik emri (taslak)</dt>
              <dd>{draftParams ? `${draftParams.safetyQty} × ${draftParams.safetyCount} @ ${draftParams.deviation}` : "—"}</dd>
            </div>
          </dl>
          <p className="helper-text">Taslak değerleri istemciden okunur; sunucu stratejisi değildir.</p>
        </section>
      )}
      {loaded && (
        <LiquidationStatusSection
          symbol={profile.pairs.length > 0 ? profile.pairs[0] : null}
          pairCount={profile.pairs.length}
          status={liquidation}
          busy={liquidationBusy}
          error={liquidationError}
          onRefresh={onRefreshLiquidation}
        />
      )}
    </section>
  );
}
