import type { ReadOnlyExplanation } from "./datasetCatalog";

type ExplanationEntry = {
  explanation: ReadOnlyExplanation;
  originalIndex: number;
};

const SEVERITY_ORDER: ReadOnlyExplanation["severity"][] = ["ERROR", "WARNING", "INFO"];

const SEVERITY_META: Record<ReadOnlyExplanation["severity"], { label: string; symbol: string }> = {
  ERROR: { label: "Teknik hata", symbol: "×" },
  WARNING: { label: "Uyarı", symbol: "!" },
  INFO: { label: "Bilgi", symbol: "i" },
};

function ExplanationCard({ explanation, originalIndex }: ExplanationEntry) {
  const meta = SEVERITY_META[explanation.severity];
  const detailsId = `historical-explanation-details-${originalIndex}`;

  return (
    <li className={`historical-explanation-card ${explanation.severity.toLowerCase()}`}>
      <div className="historical-explanation-card-heading">
        <span className="historical-explanation-symbol" aria-hidden="true">{meta.symbol}</span>
        <span className="historical-explanation-severity">{meta.label}</span>
      </div>
      <p className="historical-explanation-title"><strong>{explanation.title}</strong></p>
      <p className="historical-explanation-message">{explanation.message}</p>
      <details className="historical-explanation-details">
        <summary aria-controls={detailsId}>Teknik ayrıntılar</summary>
        <div id={detailsId} className="historical-explanation-technical">
          <dl>
            <div><dt>Kod</dt><dd><code>{explanation.code}</code></dd></div>
            <div><dt>Kaynak</dt><dd><code>{explanation.source}</code></dd></div>
            <div><dt>Bağlam</dt><dd><pre>{JSON.stringify(explanation.context, null, 2)}</pre></dd></div>
          </dl>
        </div>
      </details>
    </li>
  );
}

function ExplanationGroup({ severity, entries }: { severity: ReadOnlyExplanation["severity"]; entries: ExplanationEntry[] }) {
  const meta = SEVERITY_META[severity];

  return (
    <div className={`historical-explanation-group ${severity.toLowerCase()}`}>
      <div className="historical-explanation-group-heading">
        <p><strong>{meta.label}</strong></p>
        <span>{entries.length.toLocaleString("tr-TR")}</span>
      </div>
      <ul className="historical-explanation-list">
        {entries.map((entry) => <ExplanationCard key={`${entry.originalIndex}-${entry.explanation.code}`} {...entry} />)}
      </ul>
    </div>
  );
}

export function ExplanationSection({ explanations }: { explanations: readonly ReadOnlyExplanation[] }) {
  const groups = SEVERITY_ORDER.map((severity) => ({
    severity,
    entries: explanations.reduce<ExplanationEntry[]>((entries, explanation, originalIndex) => {
      if (explanation.severity === severity) entries.push({ explanation, originalIndex });
      return entries;
    }, []),
  })).filter((group) => group.entries.length > 0);

  return (
    <section className="historical-explanations" aria-labelledby="historical-explanations-title">
      <div className="historical-explanations-heading">
        <div>
          <p className="preflight-section-label">SONUÇ AÇIKLAMALARI</p>
          <h6 id="historical-explanations-title">Backend açıklamaları</h6>
        </div>
        <span className="historical-explanations-count">{explanations.length.toLocaleString("tr-TR")} kayıt</span>
      </div>
      <p className="historical-explanations-intro">Bu bölüm backend’in verdiği durum ve sınır açıklamalarını gösterir; UI yeni finansal hesap veya yorum üretmez.</p>
      {groups.length === 0 ? <p className="catalog-empty historical-explanations-empty">Ek açıklama bulunmuyor.</p> : <div className="historical-explanation-groups">{groups.map((group) => <ExplanationGroup key={group.severity} {...group} />)}</div>}
    </section>
  );
}
