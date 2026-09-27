import { useState } from "react";

import type { DashboardView } from "./DashboardPanel";
import type { CenterEventView } from "./EventPanel";
import type { CanaryStatusView } from "./RiskPanel";

/**
 * Faz 17 AA.9 (Durum Asistanı, ilk sürüm): LLM'siz, kural-tabanlı/
 * deterministik soru-cevap. Yalnız 3 mevcut, zaten yüklenmiş salt-okunur
 * kaynaktan beslenir (`/api/dashboard`, `/api/events`, `/api/risk/canary`) --
 * yeni backend YOK. Cevaplar sunucu verisinin aynen gösterimi + sabit metin
 * şablonlarıdır; burada hiçbir finansal hesap ya da hüküm YOK. Gerçek bir
 * dış-LLM entegrasyonu ayrı, henüz açılmamış bir ürün kararı (Arda'ya açık
 * soru, TASK.md) -- "karar/kanıt gezgini" de aynı sebeple bu sürümde yok
 * (backend'i henüz yok).
 */

export type AssistantQuestionId =
  | "durum-ne"
  | "canary-durumu"
  | "son-olaylar"
  | "bot-deal"
  | "veri-hazir"
  | "kill-switch";

type Question = { id: AssistantQuestionId; label: string };

const QUESTIONS: Question[] = [
  { id: "durum-ne", label: "Durum ne?" },
  { id: "canary-durumu", label: "Canary durumu?" },
  { id: "son-olaylar", label: "Son olaylar?" },
  { id: "bot-deal", label: "Kaç bot/deal var?" },
  { id: "veri-hazir", label: "Veri hazır mı?" },
  { id: "kill-switch", label: "Kill-switch açık mı?" },
];

function formatByStatus(byStatus: Record<string, number>): string {
  const entries = Object.entries(byStatus);
  if (entries.length === 0) return "durum dağılımı yok";
  return entries.map(([status, count]) => `${status}: ${count}`).join(" · ");
}

function formatEvent(event: CenterEventView): string {
  return `#${event.seq} ${event.kind} — ${event.ref}: ${event.summary}`;
}

type AssistantPanelProps = {
  dashboard: DashboardView | null;
  dashboardError: string;
  events: CenterEventView[];
  eventsError: string;
  canary: CanaryStatusView | null;
  canaryError: string;
  busy: boolean;
  onRefresh: () => void;
};

/** Her soru için: kaynak veri yoksa dürüst-boş metin, varsa sunucu
 * alanlarının aynen birleştirilmesi. Hiçbir dalda hesap/karşılaştırma/
 * yüzde/oran YOK -- yalnız string birleştirme. */
function answerFor(question: AssistantQuestionId, props: AssistantPanelProps): string {
  const { dashboard, dashboardError, events, eventsError, canary, canaryError } = props;
  switch (question) {
    case "durum-ne": {
      if (dashboard === null) {
        return dashboardError ? `Özet okunamadı: ${dashboardError}` : "Özet henüz okunmadı — Genel Bakış'ı yenileyin.";
      }
      const canaryPart = canary === null ? "canary henüz okunmadı" : `canary: ${canary.verdict}`;
      return `Bot: ${dashboard.bots.bots} (${dashboard.bots.bound_sessions} bağlı oturum) · `
        + `Deal: ${dashboard.deals.deals} (${formatByStatus(dashboard.deals.by_status)}) · `
        + `Paper: ${dashboard.paper.sessions} oturum, ${dashboard.paper.total_cash} nakit · `
        + canaryPart + ".";
    }
    case "canary-durumu": {
      if (canary === null) {
        return canaryError ? `Canary okunamadı: ${canaryError}` : "Canary durumu henüz okunmadı.";
      }
      const reasons = canary.reasons.length > 0 ? canary.reasons.join(" · ") : "gerekçe yok";
      return `Verdict: ${canary.verdict} · Kill-switch: ${canary.kill_switch_engaged ? "AÇIK" : "kapalı"} · `
        + `Onay: ${canary.approval_present ? "var" : "yok"} · Spec: ${canary.spec_status} · `
        + `Paper dolum sayısı: ${canary.paper_fill_count} · Gerekçe: ${reasons} · `
        + `Gözlem zamanı: ${canary.observed_at}.`;
    }
    case "son-olaylar": {
      if (events.length === 0) {
        return eventsError ? `Olaylar okunamadı: ${eventsError}` : "Henüz kaydedilmiş olay yok.";
      }
      return events.slice(0, 5).map(formatEvent).join("\n");
    }
    case "bot-deal": {
      if (dashboard === null) {
        return dashboardError ? `Özet okunamadı: ${dashboardError}` : "Özet henüz okunmadı.";
      }
      return `${dashboard.bots.bots} bot (${dashboard.bots.bound_sessions} bağlı oturum), `
        + `${dashboard.deals.deals} deal (${formatByStatus(dashboard.deals.by_status)}).`;
    }
    case "veri-hazir": {
      if (dashboard === null) {
        return dashboardError ? `Özet okunamadı: ${dashboardError}` : "Özet henüz okunmadı.";
      }
      return `Paper: ${dashboard.paper.sessions} oturum, ${dashboard.paper.positions} pozisyon, `
        + `${dashboard.paper.open_orders} açık emir · Yedek: ${dashboard.backups.backups} kayıt.`;
    }
    case "kill-switch": {
      if (canary === null) {
        return canaryError ? `Canary okunamadı: ${canaryError}` : "Kill-switch durumu henüz okunmadı.";
      }
      return canary.kill_switch_engaged
        ? "Kill-switch AÇIK — hiçbir gerçek emir gönderilmez."
        : "Kill-switch kapalı.";
    }
  }
}

export function AssistantPanel({ busy, onRefresh, ...rest }: AssistantPanelProps) {
  const [selected, setSelected] = useState<AssistantQuestionId | null>(null);
  const answer = selected === null ? null : answerFor(selected, { busy, onRefresh, ...rest });

  return (
    <section className="panel assistant-panel" aria-labelledby="assistant-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">DURUM ASİSTANI · KURAL-TABANLI</p>
          <h2 id="assistant-title">Hazır sorular</h2>
        </div>
      </div>
      <p className="helper-text">
        LLM yok — yalnız mevcut özet/olay/canary verisinin sabit şablonlarla gösterimi. Hesap veya yorum yapılmaz.
      </p>
      <button className="secondary-button" type="button" disabled={busy} onClick={onRefresh}>
        {busy ? "Yenileniyor…" : "Verileri yenile"}
      </button>
      <div className="chip-row" role="group" aria-label="Hazır sorular">
        {QUESTIONS.map((question) => (
          <button
            key={question.id}
            type="button"
            className="chip-button"
            aria-pressed={selected === question.id}
            onClick={() => setSelected(question.id)}
          >
            {question.label}
          </button>
        ))}
      </div>
      {selected !== null && (
        <div className="assistant-answer" role="status">
          <pre>{answer}</pre>
        </div>
      )}
      {selected === null && (
        <div className="empty-state" role="status">Bir soru seçin.</div>
      )}
    </section>
  );
}
