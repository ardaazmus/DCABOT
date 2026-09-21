import { useState } from "react";

import type { BotRegisterPayload } from "./BotPanel";
import {
  AdvancedDetails,
  CalculatedPreview,
  FieldGroup,
  NumericParameter,
  RiskCritical,
  TextParameter,
} from "./forms";

/**
 * Faz 11 madde 4: yeni bot 5 adımlı sihirbaz + sağda canlı önizleme.
 * İstemci doğrulaması backend kurallarının aynasıdır (bot_registry);
 * yetki backend'dedir, burası yalnız rehberlik eder.
 */

const IDENTIFIER = /^[A-Za-z0-9_.:-]{1,100}$/;
const SYMBOL = /^[A-Z0-9]{3,20}$/;
const DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;

export type WizardDraft = {
  botId: string;
  name: string;
  pairs: string;
  blacklist: string;
  favorites: string;
  budget: string;
};

const INITIAL_DRAFT: WizardDraft = {
  botId: "",
  name: "",
  pairs: "",
  blacklist: "",
  favorites: "",
  budget: "",
};

function parseCsv(raw: string): string[] {
  return raw.split(",").map((s) => s.trim()).filter((s) => s.length > 0);
}

function stepError(step: number, draft: WizardDraft): string {
  if (step === 0) {
    if (!IDENTIFIER.test(draft.botId.trim())) return "Bot kimliği geçersiz (harf/rakam/._:- , 1-100 karakter).";
    if (draft.name.trim().length === 0) return "Bot adı boş olamaz.";
    return "";
  }
  if (step === 1) {
    const pairs = parseCsv(draft.pairs);
    if (pairs.length === 0 || pairs.length > 32) return "Pair listesi 1-32 sembol olmalıdır.";
    if (new Set(pairs).size !== pairs.length) return "Pair listesi benzersiz semboller içermelidir.";
    if (!pairs.every((s) => SYMBOL.test(s))) return "Sembol biçimi geçersiz (A-Z/0-9, 3-20 karakter).";
    return "";
  }
  if (step === 2) {
    for (const [label, raw] of [["Blacklist", draft.blacklist], ["Favoriler", draft.favorites]] as const) {
      const list = parseCsv(raw);
      if (list.length > 32 || new Set(list).size !== list.length) return `${label}: en fazla 32 benzersiz sembol.`;
      if (!list.every((s) => SYMBOL.test(s))) return `${label}: sembol biçimi geçersiz.`;
    }
    return "";
  }
  if (step === 3) {
    if (!DECIMAL.test(draft.budget.trim())) return "Bütçe exact decimal metni olmalıdır (negatif yok).";
    return "";
  }
  return "";
}

const STEPS = ["Kimlik", "Pariteler", "Listeler", "Bütçe", "Önizleme"];

export function BotWizard({ busy, error, onRegister }: {
  busy: boolean;
  error: string;
  onRegister: (payload: BotRegisterPayload) => void;
}) {
  const [draft, setDraft] = useState<WizardDraft>(INITIAL_DRAFT);
  const [step, setStep] = useState(0);
  const [stepIssue, setStepIssue] = useState("");

  function update(key: keyof WizardDraft, value: string) {
    setDraft((current) => ({ ...current, [key]: value }));
    setStepIssue("");
  }

  function go(delta: number) {
    if (delta > 0) {
      const issue = stepError(step, draft);
      if (issue) {
        setStepIssue(issue);
        return;
      }
    }
    setStepIssue("");
    setStep((current) => Math.min(Math.max(current + delta, 0), STEPS.length - 1));
  }

  function submit() {
    for (let s = 0; s < STEPS.length - 1; s += 1) {
      const issue = stepError(s, draft);
      if (issue) {
        setStep(s);
        setStepIssue(issue);
        return;
      }
    }
    onRegister({
      bot_id: draft.botId.trim(),
      name: draft.name.trim(),
      pairs: parseCsv(draft.pairs),
      blacklist: parseCsv(draft.blacklist),
      favorites: parseCsv(draft.favorites),
      virtual_quote_budget: draft.budget.trim(),
    });
  }

  const pairCount = parseCsv(draft.pairs).length;

  return (
    <section className="panel rebalance-panel" aria-labelledby="bot-wizard-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">YENİ BOT</p>
          <h2 id="bot-wizard-title">Bot kayıt sihirbazı</h2>
        </div>
        <span className="state-label" aria-live="polite">Adım {step + 1}/{STEPS.length} · {STEPS[step]}</span>
      </div>
      {error && <div className="form-error" role="alert">{error}</div>}
      {stepIssue && <div className="form-error" role="alert">{stepIssue}</div>}
      <div className="wizard-layout">
        <div className="wizard-steps">
          {step === 0 && <FieldGroup label="1 · Kimlik">
            <TextParameter label="Bot kimliği" name="wizard_bot_id" value={draft.botId} onChange={(v) => update("botId", v)} />
            <TextParameter label="Bot adı" name="wizard_bot_name" value={draft.name} onChange={(v) => update("name", v)} />
          </FieldGroup>}
          {step === 1 && <FieldGroup label="2 · Pariteler">
            <TextParameter label="Pair listesi (virgülle)" name="wizard_pairs" value={draft.pairs} onChange={(v) => update("pairs", v)} />
          </FieldGroup>}
          {step === 2 && <FieldGroup label="3 · Listeler (opsiyonel)">
            <AdvancedDetails title="Gelişmiş: liste yönetimi">
              <TextParameter label="Blacklist" name="wizard_blacklist" value={draft.blacklist} onChange={(v) => update("blacklist", v)} />
              <TextParameter label="Favoriler" name="wizard_favorites" value={draft.favorites} onChange={(v) => update("favorites", v)} />
            </AdvancedDetails>
          </FieldGroup>}
          {step === 3 && <FieldGroup label="4 · Bütçe">
            <RiskCritical label="Sanal bütçe">
              <NumericParameter label="Sanal bütçe" name="wizard_budget" value={draft.budget} suffix="USDT" onChange={(v) => update("budget", v)} />
            </RiskCritical>
          </FieldGroup>}
          {step === 4 && <FieldGroup label="5 · Önizleme ve onay">
            <CalculatedPreview label="Bot" value={draft.botId.trim() || "—"} note={draft.name.trim() || "adsız"} />
            <CalculatedPreview label="Pair sayısı" value={String(pairCount)} />
            <CalculatedPreview label="Sanal bütçe" value={draft.budget.trim() || "—"} unit="USDT" />
            <p className="helper-text">Kayıt yalnız yerel bot kaydını oluşturur; emir vermez, session bağlamaz.</p>
          </FieldGroup>}
          <div className="wizard-nav">
            <button className="secondary-button" type="button" disabled={step === 0 || busy} onClick={() => go(-1)}>Geri</button>
            {step < STEPS.length - 1
              ? <button className="secondary-button" type="button" disabled={busy} onClick={() => go(1)}>İleri</button>
              : <button className="primary-button" type="button" disabled={busy} onClick={submit}>Botu kaydet</button>}
          </div>
        </div>
        <aside className="wizard-preview" aria-label="Canlı önizleme">
          <h3 className="paper-subheading">Canlı önizleme</h3>
          <CalculatedPreview label="Kimlik" value={draft.botId.trim() || "—"} note="girilen değer" />
          <CalculatedPreview label="Pair" value={String(pairCount)} note="virgülle ayrılmış" />
          <CalculatedPreview label="Bütçe" value={draft.budget.trim() || "—"} unit="USDT" />
        </aside>
      </div>
    </section>
  );
}
