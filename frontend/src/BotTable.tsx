import { useDeferredValue, useState } from "react";

import type { BotProfileView } from "./BotPanel";

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

export function BotTable({ rows, busy, onSelect }: {
  rows: BotTableRow[];
  busy: boolean;
  onSelect: (botId: string) => void;
}) {
  const [filter, setFilter] = useState("");
  const deferredFilter = useDeferredValue(filter);
  const needle = deferredFilter.trim().toLocaleLowerCase("tr-TR");
  const visible = needle
    ? rows.filter((row) => row.botId.toLocaleLowerCase("tr-TR").includes(needle))
    : rows;

  return (
    <section className="panel rebalance-panel" aria-labelledby="bot-table-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">FLEET OPS</p>
          <h2 id="bot-table-title">Bot tablosu</h2>
        </div>
        <span className="state-label">{visible.length}/{rows.length}</span>
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
        <div className="empty-state">Kayıtlı bot yok — sihirbazla kaydedin.</div>
      ) : visible.length === 0 ? (
        <div className="empty-state">Filtreye uyan bot yok.</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Bot</th>
                <th>Ad</th>
                <th>Session</th>
                <th>Durum</th>
                <th>İşlem</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => (
                <tr key={row.botId}>
                  <td>{row.botId}</td>
                  <td>{row.name ?? "—"}</td>
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
