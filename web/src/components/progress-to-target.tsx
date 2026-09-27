import { percentToWidth } from "@/lib/chart/percent";
import {
  formatDecimal,
  parseDecimal,
  type DecimalString,
} from "@/lib/decimal";
import { cn } from "@/lib/utils";

export function ProgressToTarget({
  /** Backend'in yüzde metni (örn. "37.5"). */
  percent,
  label,
  className,
}: {
  percent: DecimalString;
  /** Ön metin ("TP'ye" gibi); verilmezse yalnız yüzde gösterilir. */
  label?: string;
  className?: string;
}) {
  const text = formatDecimal(parseDecimal(percent), { maxFractionDigits: 1 });
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuetext={`%${text}`}
        className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted"
      >
        <div
          className="h-full rounded-full bg-profit"
          style={{ width: percentToWidth(percent) }}
        />
      </div>
      <span className="font-mono text-xs whitespace-nowrap text-muted-foreground">
        {label === undefined ? `%${text}` : `${label} %${text}`}
      </span>
    </div>
  );
}
