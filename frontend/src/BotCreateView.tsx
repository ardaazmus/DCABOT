import type { ReactNode } from "react";

import type { CandleStatus } from "./CandleChart";
import type { HistoricalChartBar } from "./datasetCatalog";
import { SegmentedControl } from "./forms";
import { HeroChartPanel } from "./HeroChartPanel";
import { useI18n } from "./i18n";

export type BotCreateType = "DCA" | "GRID" | "FUTURES" | "SIGNAL";

/**
 * Faz 15.3: tek-amaç "Bot Oluştur" görünümü — referanslardaki "Create Bot"
 * deneyimi: üstte tip seçici, solda form (~%35), sağda grafik (~%65), altta
 * veri-aralığı + hazır rozeti + backtest. Formlar mevcut panellerin
 * kendisidir (kopya yok): DCA→BotWizard, Grid/Futures→FuturesPanel,
 * Signal→SignalPanel. Futures formu 15.3b'de Pionex yerleşimine kavuşur.
 */
export function BotCreateView({
  botType,
  onBotTypeChange,
  onBack,
  onOpenBacktest,
  bars,
  chartStatus,
  chartError,
  livePrice,
  symbolLabel,
  canLoadChart,
  chartLoading,
  onLoadChart,
  dataRange,
  backtestReady,
  renderForm,
}: {
  botType: BotCreateType;
  onBotTypeChange: (next: BotCreateType) => void;
  onBack: () => void;
  onOpenBacktest: () => void;
  bars: HistoricalChartBar[];
  chartStatus: CandleStatus;
  chartError: string;
  livePrice: string | null;
  symbolLabel: string;
  canLoadChart: boolean;
  chartLoading: boolean;
  onLoadChart: () => void;
  dataRange: string | null;
  backtestReady: boolean;
  renderForm: (botType: BotCreateType) => ReactNode;
}) {
  const { t } = useI18n();
  return (
    <section className="bot-create-view" aria-labelledby="bot-create-title">
      <div className="bot-create-head">
        <button className="secondary-button" type="button" onClick={onBack}>
          {t("create.back.label")}
        </button>
        <h2 id="bot-create-title">{t("create.title")}</h2>
      </div>
      <div className="bot-create-type">
        <SegmentedControl
          label={t("create.type.label")}
          name="bot_create_type"
          value={botType}
          options={[
            { value: "DCA", label: t("create.type.dca") },
            { value: "GRID", label: t("create.type.grid") },
            { value: "FUTURES", label: t("create.type.futures") },
            { value: "SIGNAL", label: t("create.type.signal") },
          ]}
          onChange={(next) => onBotTypeChange(next as BotCreateType)}
        />
      </div>
      <div className="bot-create-grid">
        <div className="bot-create-form">{renderForm(botType)}</div>
        <div className="bot-create-chart">
          <HeroChartPanel
            bars={bars}
            status={chartStatus}
            error={chartError}
            livePrice={livePrice}
            symbolLabel={symbolLabel}
            canLoad={canLoadChart}
            loadBusy={chartLoading}
            onLoad={onLoadChart}
          />
        </div>
      </div>
      <div className="bot-create-footer">
        <span className="data-range-badge">
          {t("create.datarange.label")}: {dataRange ?? "—"}
        </span>
        {backtestReady ? (
          <span className="state-label ready" role="status">{t("create.ready.label")}</span>
        ) : (
          <span className="state-label" role="status">{t("create.notready.label")}</span>
        )}
        <button className="secondary-button" type="button" onClick={onOpenBacktest}>
          {t("backtest.button.label")}
        </button>
      </div>
    </section>
  );
}
