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

/* Faz 15.2: sektör-standardı kontroller (3Commas/Pionex/Bitsgap dili).
 * Para kuralı: oran eşlemesi YALNIZ exact metin tablosuyla yapılır; UI'da
 * finansal hesap ve float geri-yazımı yok. Slider konumu (piksel) için
 * parseFloat yalnız gösterimde kullanılır, asla geri yazılmaz (CandleChart
 * ile aynı disiplin). Tam-sayı adım aritmetiği girdi-doğrulama kategorisidir
 * (BotWizard COUNT kontrolüyle aynı emsal). */

export type SegmentOption = { value: string; label: string; disabled?: boolean };

export function SegmentedControl({ label, name, value, options, onChange }: {
  label: string;
  name: string;
  value: string;
  options: SegmentOption[];
  onChange: (value: string) => void;
}) {
  return (
    <div className="segmented-field">
      <span className="field-label" id={`${name}-label`}>{label}</span>
      <div className="segmented-control" role="radiogroup" aria-labelledby={`${name}-label`}>
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={value === option.value}
            aria-disabled={option.disabled === true}
            disabled={option.disabled === true}
            className="segment-option"
            onClick={() => { if (option.disabled !== true) onChange(option.value); }}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export type PercentChip = { chip: string; ratio: string };

export function QuickPercentChips({ label, options, onSelect }: {
  label: string;
  options: PercentChip[];
  onSelect: (ratio: string) => void;
}) {
  return (
    <div className="percent-chips-field">
      <span className="field-label">{label}</span>
      <div className="percent-chips" role="group" aria-label={label}>
        {options.map((option) => (
          <button key={option.chip} type="button" className="chip-button" onClick={() => onSelect(option.ratio)}>
            {option.chip}
          </button>
        ))}
      </div>
    </div>
  );
}

export function ToggleSwitchRow({ label, checked, onChange, hint }: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  hint?: string;
}) {
  return (
    <div className="toggle-row">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        className="toggle-switch"
        onClick={() => onChange(!checked)}
      >
        <span className="toggle-knob" aria-hidden="true" />
      </button>
      <span className="toggle-label">{label}</span>
      {hint && <span className="toggle-hint">{hint}</span>}
    </div>
  );
}

const STEPPER_INT = /^(?:0|[1-9]\d*)$/;

export function StepperInput({ label, name, value, min = "0", max, step = "1", onChange }: {
  label: string;
  name: string;
  value: string;
  min?: string;
  max?: string;
  step?: string;
  onChange: (value: string) => void;
}) {
  function shift(delta: number) {
    const minInt = Number(min);
    const maxInt = max === undefined ? null : Number(max);
    const stepInt = Number(step);
    const current = STEPPER_INT.test(value.trim()) ? Number(value.trim()) : null;
    let next = current === null ? (delta > 0 ? minInt + stepInt : minInt) : current + delta * stepInt;
    if (next < minInt) next = minInt;
    if (maxInt !== null && next > maxInt) next = maxInt;
    onChange(String(next));
  }
  return (
    <div className="stepper-field">
      <span className="field-label">{label}</span>
      <div className="stepper">
        <button type="button" className="stepper-button" aria-label={`${label} azalt`} onClick={() => shift(-1)}>
          −
        </button>
        <input aria-label={label} name={name} value={value} inputMode="numeric" onChange={(event) => onChange(event.target.value)} />
        <button type="button" className="stepper-button" aria-label={`${label} artır`} onClick={() => shift(1)}>
          +
        </button>
      </div>
    </div>
  );
}

const SLIDER_DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;

export function BudgetSlider({ label, name, value, max = "10000", step = "10", onChange }: {
  label: string;
  name: string;
  value: string;
  max?: string;
  step?: string;
  onChange: (value: string) => void;
}) {
  const stopCount = Math.max(1, Math.floor(Number(max) / Number(step)));
  const parsed = SLIDER_DECIMAL.test(value.trim()) ? parseFloat(value.trim()) : 0;
  const position = Math.max(0, Math.min(stopCount, Math.round(parsed / Number(step))));
  return (
    <div className="slider-field budget-slider-field">
      <span className="field-label">{label}</span>
      <div className="slider-row">
        <input
          type="range"
          aria-label={`${label} kaydırıcı`}
          min={0}
          max={stopCount}
          step={1}
          value={position}
          onChange={(event) => onChange(String(Number(event.target.value) * Number(step)))}
        />
        <span className="input-wrap slider-input-wrap">
          <input aria-label={label} name={name} value={value} inputMode="decimal" onChange={(event) => onChange(event.target.value)} />
          <span className="suffix">USDT</span>
        </span>
      </div>
    </div>
  );
}

export function LabeledSlider({ label, name, value, stops, minLabel, maxLabel, onChange }: {
  label: string;
  name: string;
  value: string;
  stops: string[];
  minLabel: string;
  maxLabel: string;
  onChange: (value: string) => void;
}) {
  if (stops.length === 0) return null;
  const found = stops.indexOf(value.trim());
  let position = found;
  if (position === -1) {
    // Liste-dışı değerde başparmak en yakın durağa yaslanır (yalnız gösterim).
    const target = SLIDER_DECIMAL.test(value.trim()) ? parseFloat(value.trim()) : NaN;
    if (Number.isNaN(target)) {
      position = 0;
    } else {
      let best = 0;
      let bestDistance = Number.POSITIVE_INFINITY;
      stops.forEach((stop, index) => {
        const distance = Math.abs(parseFloat(stop) - target);
        if (distance < bestDistance) {
          bestDistance = distance;
          best = index;
        }
      });
      position = best;
    }
  }
  return (
    <div className="slider-field">
      <span className="field-label">{label}</span>
      <div className="slider-labels">
        <span>{minLabel}</span>
        <strong>{value.trim() === "" ? "—" : value.trim()}</strong>
        <span>{maxLabel}</span>
      </div>
      <input
        type="range"
        aria-label={label}
        name={name}
        min={0}
        max={stops.length - 1}
        step={1}
        value={position}
        onChange={(event) => onChange(stops[Number(event.target.value)] ?? stops[0])}
      />
    </div>
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
