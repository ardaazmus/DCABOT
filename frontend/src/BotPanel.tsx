import { useState } from "react";
import { AdvancedDetails, FieldGroup, NumericParameter, RiskCritical, TextParameter } from "./forms";

export type BotProfileView = {
  bot_id: string;
  name: string;
  pairs: string[];
  blacklist: string[];
  favorites: string[];
  virtual_quote_budget: string;
};

export type BotCheckView = {
  bot_id: string;
  symbol: string;
  verdict: string;
  reason: string;
};

export type BotRegisterPayload = {
  bot_id: string;
  name: string;
  pairs: string[];
  blacklist: string[];
  favorites: string[];
  virtual_quote_budget: string;
};

export type BotListsPayload = {
  blacklist: string[];
  favorites: string[];
};

export type BotBindPayload = {
  session_id: string;
  symbol: string;
};

function isStringList(value: unknown): value is string[] {
  return Array.isArray(value) && (value as unknown[]).every((s) => typeof s === "string");
}

export function isBotProfileView(value: unknown): value is BotProfileView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.bot_id === "string" &&
    typeof body.name === "string" &&
    isStringList(body.pairs) &&
    isStringList(body.blacklist) &&
    isStringList(body.favorites) &&
    typeof body.virtual_quote_budget === "string"
  );
}

export function isBotCheckView(value: unknown): value is BotCheckView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.bot_id === "string" &&
    typeof body.symbol === "string" &&
    typeof body.verdict === "string" &&
    typeof body.reason === "string"
  );
}

function parseCsv(raw: string): string[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

export function BotPanel({
  botIds,
  profile,
  sessions,
  check,
  busy,
  error,
  onRegister,
  onSelect,
  onUpdateLists,
  onBind,
  onCheck,
  onRefresh,
}: {
  botIds: string[];
  profile: BotProfileView | null;
  sessions: Record<string, string>;
  check: BotCheckView | null;
  busy: boolean;
  error: string;
  onRegister: (payload: BotRegisterPayload) => void;
  onSelect: (botId: string) => void;
  onUpdateLists: (payload: BotListsPayload) => void;
  onBind: (payload: BotBindPayload) => void;
  onCheck: (symbol: string) => void;
  onRefresh: () => void;
}) {
  const [botId, setBotId] = useState("bot-1");
  const [name, setName] = useState("Grid Alpha");
  const [pairs, setPairs] = useState("BTCUSDT, ETHUSDT");
  const [budget, setBudget] = useState("10000");
  const [blacklist, setBlacklist] = useState("LUNAUSDT");
  const [favorites, setFavorites] = useState("BTCUSDT");
  const [sessionId, setSessionId] = useState("sess-1");
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [formError, setFormError] = useState("");

  function submitRegister() {
    const pairList = parseCsv(pairs);
    if (!botId.trim() || !name.trim() || pairList.length === 0) {
      setFormError("Bot kimliği, ad ve en az bir pair gerekli.");
      return;
    }
    setFormError("");
    onRegister({
      bot_id: botId.trim(),
      name: name.trim(),
      pairs: pairList,
      blacklist: parseCsv(blacklist),
      favorites: parseCsv(favorites),
      virtual_quote_budget: budget.trim(),
    });
  }

  function submitBind() {
    if (!sessionId.trim() || !symbol.trim()) {
      setFormError("Session kimliği ve sembol boş olamaz.");
      return;
    }
    setFormError("");
    onBind({ session_id: sessionId.trim(), symbol: symbol.trim() });
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="bots-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">BOT FLEET</p>
          <h2 id="bots-title">Çoklu bot kaydı ve sahiplik</h2>
        </div>
      </div>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      {formError && (
        <div className="form-error" role="alert">
          {formError}
        </div>
      )}

      <FieldGroup id="bot-register" label="Bot kaydı">
        <TextParameter label="Bot kimliği" name="bot_id" value={botId} onChange={setBotId} />
        <TextParameter label="Bot adı" name="bot_name" value={name} onChange={setName} />
        <TextParameter label="Pair listesi" name="bot_pairs" value={pairs} onChange={setPairs} />
        <RiskCritical label="Sanal bütçe">
          <NumericParameter label="Sanal bütçe" name="bot_budget" value={budget} suffix="USDT" onChange={setBudget} />
        </RiskCritical>
      </FieldGroup>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitRegister}>
        Bot kaydet
      </button>
      <button className="secondary-button" type="button" disabled={busy} onClick={onRefresh}>
        Listeyi yenile
      </button>

      <AdvancedDetails title="Gelişmiş: liste yönetimi">
        <FieldGroup id="bot-lists" label="Blacklist / favoriler">
          <TextParameter label="Blacklist" name="bot_blacklist" value={blacklist} onChange={setBlacklist} />
          <TextParameter label="Favoriler" name="bot_favorites" value={favorites} onChange={setFavorites} />
        </FieldGroup>
      </AdvancedDetails>
      <button
        className="secondary-button"
        type="button"
        disabled={busy}
        onClick={() => {
          setFormError("");
          onUpdateLists({ blacklist: parseCsv(blacklist), favorites: parseCsv(favorites) });
        }}
      >
        Listeleri güncelle
      </button>

      <FieldGroup id="bot-sessions" label="Session sahipliği">
        <TextParameter label="Session kimliği" name="bot_session" value={sessionId} onChange={setSessionId} />
        <TextParameter label="Sembol" name="bot_symbol" value={symbol} onChange={setSymbol} />
      </FieldGroup>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitBind}>
        Session bağla
      </button>
      <button
        className="secondary-button"
        type="button"
        disabled={busy}
        onClick={() => {
          if (!symbol.trim()) {
            setFormError("Sembol boş olamaz.");
            return;
          }
          setFormError("");
          onCheck(symbol.trim());
        }}
      >
        Pair kontrolü
      </button>

      {profile && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Seçili bot</td>
                <td>
                  {profile.bot_id} · {profile.name}
                </td>
              </tr>
              <tr>
                <td>Bütçe</td>
                <td>{profile.virtual_quote_budget}</td>
              </tr>
              <tr>
                <td>Session sayısı</td>
                <td>{Object.keys(sessions).length}</td>
              </tr>
            </tbody>
          </table>
          <p className="paper-note">
            Bir session yalnız bir botun olabilir; blacklist kapsamla kesişemez, favoriler kapsam içindedir.
          </p>
        </div>
      )}
      {check && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Pair kararı</td>
                <td>
                  {check.symbol}: {check.verdict}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
      {botIds.length > 0 && (
        <FieldGroup label="Bot seç">
          <TextParameter label="Bot seç" name="bot_pick" value={botId} onChange={setBotId} />
        </FieldGroup>
      )}
      {botIds.length > 0 && (
        <button
          className="secondary-button"
          type="button"
          disabled={busy}
          onClick={() => {
            if (!botId.trim()) {
              setFormError("Bot kimliği boş olamaz.");
              return;
            }
            setFormError("");
            onSelect(botId.trim());
          }}
        >
          Botu yükle
        </button>
      )}
    </section>
  );
}
