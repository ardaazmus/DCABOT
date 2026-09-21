import { useDeferredValue, useState } from "react";

import type { BotProfileView } from "./BotPanel";
import { STRATEGY_DRAFT_PREFIX } from "./BotWizard";
import { useI18n } from "./i18n";

/**
 * Faz 11 madde 5: kart-özet yerine table-first operasyonel yüzey.
 * Satırlar yalnız kayıtlı kimlik + seçili botun yüklenmiş detayını
 * gösterir; yüklenmemiş botlarda bilinmeyen alan "—" kalır.
 */

export type BotTableRow = {
  botId: string;
  name: string | null;
  sessionCount: number | null;
  selected: boolean;
};

/**
 * Faz 15.3: kayıt anındaki bot tipi istemci taslağından okunur (sunucu
 * sözleşmesinde tip yok). Okuma başarısız olursa "—" gösterilir, satır
 * uydurulmaz; tipsiz botlar yalnız "Tümü" filtresinde görünür.
 */
export function readDraftBotType(botId: string): string | null {
  try {
    const raw = window.localStorage.getItem(`${STRATEGY_DRAFT_PREFIX}${botId}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { botType?: unknown };
    return typeof parsed.botType === "string" ? parsed.botType : null;
  } catch {
    return null;
  }
}

type FleetTab = "active" | "history";
type FleetFilter = "ALL" | "DCA" | "GRID" | "FUTURES" | "SIGNAL";

export function BotTable({ rows, busy, onSelect, onCreate, onOpenHistory }: {
  rows: BotTableRow[];
  busy: boolean;
  onSelect: (botId: string) => void;
  onCreate: () => void;
  onOpenHistory: () => void;
}) {
  const { t } = useI18n();
  const [tab, setTab] = useState<FleetTab>("active");
  const [typeFilter, setTypeFilter] = useState<FleetFilter>("ALL");
  const [filter, setFilter] = useState("");
  const deferredFilter = useDeferredValue(filter);
  const needle = deferredFilter.trim().toLocaleLowerCase("tr-TR");
  const typed = rows.map((row) => ({ row, botType: readDraftBotType(row.botId) }));
  const visible = typed.filter(({ row, botType }) => {
    if (typeFilter !== "ALL" && botType !== typeFilter) return false;
    if (needle && !row.botId.toLocaleLowerCase("tr-TR").includes(needle)) return false;
    return true;
  });

  function typeLabel(botType: string | null): string {
    if (botType === "DCA") return t("fleet.filter.dca");
    if (botType === "GRID") return t("fleet.filter.grid");
    if (botType === "FUTURES") return t("fleet.filter.futures");
    if (botType === "SIGNAL") return t("fleet.filter.signal");
    return "—";
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="bot-table-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">FLEET OPS</p>
          <h2 id="bot-table-title">Bot tablosu</h2>
        </div>
        <span className="state-label">{visible.length}/{rows.length}</span>
      </div>
      <div className="fleet-tabs" role="tablist" aria-label="Bot listesi">
        <button type="button" role="tab" aria-selected={tab === "active"} className="fleet-tab" onClick={() => setTab("active")}>
          {t("fleet.active.label")}
        </button>
        <button type="button" role="tab" aria-selected={tab === "history"} className="fleet-tab" onClick={() => setTab("history")}>
          {t("fleet.history.label")}
        </button>
      </div>
      {tab === "history" ? (
        <div className="fleet-empty" role="tabpanel">
          <p className="helper-text">{t("fleet.history.note")}</p>
          <button className="secondary-button" type="button" onClick={onOpenHistory}>
            {t("fleet.history.open")}
          </button>
        </div>
      ) : (
        <>
          <div className="fleet-filters" role="group" aria-label="Tip filtresi">
            {(
              [
                ["ALL", t("fleet.filter.all")],
                ["DCA", t("fleet.filter.dca")],
                ["GRID", t("fleet.filter.grid")],
                ["FUTURES", t("fleet.filter.futures")],
                ["SIGNAL", t("fleet.filter.signal")],
              ] as [FleetFilter, string][]
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                className="chip-button"
                aria-pressed={typeFilter === value}
                onClick={() => setTypeFilter(value)}
              >
                {label}
              </button>
            ))}
          </div>
          <label className="field">
            <span className="field-label">Filtre (bot kimliği)</span>
            <span className="input-wrap">
              <input
                aria-label="Filtre (bot kimliği)"
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
                placeholder="örn. bot-"
              />
            </span>
          </label>
          {rows.length === 0 ? (
            <div className="fleet-empty" role="status">
              <p className="fleet-empty-icon" aria-hidden="true">▣</p>
              <p className="fleet-empty-title">{t("fleet.empty.title")}</p>
              <p className="helper-text">{t("fleet.empty.body")}</p>
              <button className="primary-button fleet-empty-cta" type="button" onClick={onCreate}>
                {t("fleet.empty.cta")}
              </button>
            </div>
          ) : visible.length === 0 ? (
            <div className="empty-state">Filtreye uyan bot yok.</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Bot</th>
                    <th>Ad</th>
                    <th>{t("fleet.type.label")}</th>
                    <th>Session</th>
                    <th>Durum</th>
                    <th>İşlem</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map(({ row, botType }) => (
                    <tr key={row.botId}>
                      <td>{row.botId}</td>
                      <td>{row.name ?? "—"}</td>
                      <td>{typeLabel(botType)}</td>
                      <td>{row.sessionCount ?? "—"}</td>
                      <td>{row.selected ? "Seçili" : "—"}</td>
                      <td>
                        <button
                          className="secondary-button"
                          type="button"
                          disabled={busy || row.selected}
                          onClick={() => onSelect(row.botId)}
                        >
                          Yükle
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  );
}

const WORKSPACE_TABS = [
  { id: "bot-register", label: "Kayıt" },
  { id: "bot-lists", label: "Listeler" },
  { id: "bot-sessions", label: "Session" },
] as const;

export function BotContextHeader({ profile, sessionCount }: {
  profile: BotProfileView | null;
  sessionCount: number;
}) {
  return (
    <section className="panel rebalance-panel" aria-labelledby="bot-context-title">
      <nav className="breadcrumb" aria-label="Konum">
        <span>Botlar &amp; Stratejiler</span>
        <span aria-hidden="true">›</span>
        <span aria-current="page">{profile?.bot_id ?? "bot seçili değil"}</span>
      </nav>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">BOT CONTEXT</p>
          <h2 id="bot-context-title">{profile ? `${profile.bot_id} · ${profile.name}` : "Bot seçili değil"}</h2>
        </div>
      </div>
      {profile ? (
        <dl className="preflight-facts">
          <div><dt>Pair</dt><dd>{profile.pairs.length}</dd></div>
          <div><dt>Session</dt><dd>{sessionCount}</dd></div>
          <div><dt>Bütçe</dt><dd>{profile.virtual_quote_budget} USDT</dd></div>
        </dl>
      ) : (
        <p className="helper-text">Detay için tablodan bir bot yükleyin.</p>
      )}
      <div className="workspace-tabs" role="navigation" aria-label="Bot bölümleri">
        {WORKSPACE_TABS.map((tab) => (
          <a key={tab.id} href={`#${tab.id}`}>{tab.label}</a>
        ))}
      </div>
    </section>
  );
}
