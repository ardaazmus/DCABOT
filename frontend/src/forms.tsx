import { createContext, useContext, type ReactNode } from "react";

/**
 * Faz 11 madde 4: tüm strateji tiplerinin paylaştığı ortak form ailesi.
 * Madde 3: progressive disclosure — "Gelişmiş: ..." en fazla 2 seviye,
 * risk-kritik alanlar hiçbir zaman katlanmaz (yapısal zorunluluk).
 */

const DisclosureDepthContext = createContext(0);

export const MAX_DISCLOSURE_DEPTH = 2;

export function Section({ id, eyebrow, title, action, children }: {
  id: string;
  eyebrow: string;
  title: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="panel rebalance-panel" aria-labelledby={id}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2 id={id}>{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function FieldGroup({ id, label, children }: { id?: string; label?: string; children: ReactNode }) {
  return (
    <div className="paper-order-form" role="group" aria-label={label}>
      {label && <h3 className="paper-subheading" id={id}>{label}</h3>}
      {children}
    </div>
  );
}

type ParameterProps = {
  label: string;
  name: string;
  value: string;
  suffix?: string;
  error?: string;
  onChange: (value: string) => void;
};

function ParameterShell({ label, name, value, suffix, error, onChange, inputMode, type, min, max }: ParameterProps & {
  inputMode?: "decimal" | "text" | "numeric";
  type?: string;
  min?: string;
  max?: string;
}) {
  return (
    <label className={`field ${error ? "has-error" : ""}`}>
      <span className="field-label">{label}</span>
      <span className="input-wrap">
        <input
          aria-label={label}
          name={name}
          value={value}
          type={type ?? "text"}
          inputMode={inputMode}
          min={min}
          max={max}
          onChange={(event) => onChange(event.target.value)}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${name}-error` : undefined}
        />
        {suffix && <span className="suffix">{suffix}</span>}
      </span>
      {error && <span className="field-error" id={`${name}-error`} role="alert">{error}</span>}
    </label>
  );
}

export function TextParameter(props: ParameterProps) {
  return <ParameterShell {...props} inputMode="text" />;
}

export function NumericParameter(props: ParameterProps & { integer?: boolean; min?: string; max?: string }) {
  const { integer, min, max, ...rest } = props;
  return (
    <ParameterShell
      {...rest}
      type={integer ? "number" : "text"}
      inputMode={integer ? "numeric" : "decimal"}
      min={min}
      max={max}
    />
  );
}

export function ConditionalField({ when, children }: { when: boolean; children: ReactNode }) {
  if (!when) return null;
  return <>{children}</>;
}

export function CalculatedPreview({ label, value, unit, note }: {
  label: string;
  value: string;
  unit?: string;
  note?: string;
}) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <strong>{value}</strong>
      {unit && <span className="metric-unit">{unit}</span>}
      {note && <span className="metric-note">{note}</span>}
    </div>
  );
}

export function AdvancedDetails({ title, children }: { title: string; children: ReactNode }) {
  const depth = useContext(DisclosureDepthContext);
  if (depth >= MAX_DISCLOSURE_DEPTH) {
    return (
      <div className="advanced-details-overflow" role="note">
        <p className="helper-text">Katman sınırı aşıldı ({title}); içerik açık gösteriliyor.</p>
        {children}
      </div>
    );
  }
  return (
    <details className="advanced-details">
      <summary>{title}</summary>
      <DisclosureDepthContext.Provider value={depth + 1}>
        {children}
      </DisclosureDepthContext.Provider>
    </details>
  );
}

/** Risk-kritik alan sarmalayıcı: katman içindeyse uyarı verir ve açık render eder. */
export function RiskCritical({ label, children }: { label: string; children: ReactNode }) {
  const depth = useContext(DisclosureDepthContext);
  if (depth === 0) return <>{children}</>;
  return (
    <div className="risk-open" role="note">
      <p className="helper-text">Risk-kritik alan katlanamaz ({label}); açık gösteriliyor.</p>
      {children}
    </div>
  );
}
