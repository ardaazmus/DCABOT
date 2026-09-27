/* Faz 17 AA.13b: portföy-halkası (qwen sec-portfolio dizilimi).
 * `GET /api/portfolio/dca-performance` — pay/oran/toplam TAMAMI sunucuda
 * hesaplı; UI yalnız sunucu metnini dizer. Halka geometrisi CandleChart
 * emsali: exact-ondalık metin → BigInt sabit-nokta → tamsayı açı; Number()
 * YALNIZ piksel-koordinatında. Negatif/sıfır/null payın yayı YOK (halka
 * negatif alanı gösteremez) — tablo her botu tam gösterir, boşluk dürüst-notla
 * açıklanır. Pozitif-pay toplamı 1'i aşarsa halka hiç çizilmez. */

const SHARE_PATTERN = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/;
const RING_CENTER = 100;
const RING_OUTER = 90;
const RING_INNER = 58;
const FULL_MDEG = 360000n;
const RING_PALETTE = ["#f5a524", "#17c964", "#06b6d4c", "#f31260", "#8b5cf6", "#0ea5e9", "#eab308", "#ec4899"];

export type PortfolioBotShare = {
  bot_id: string;
  realized_net: string;
  share_of_total: string | null;
};

export type PortfolioDcaPerformance = {
  bot_count: number;
  winning_bot_count: number;
  total_realized_net: string;
  bots: PortfolioBotShare[];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isCount(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value);
}

function isBotShare(value: unknown): value is PortfolioBotShare {
  if (!isRecord(value)) return false;
  return typeof value.bot_id === "string"
    && typeof value.realized_net === "string"
    && (typeof value.share_of_total === "string" || value.share_of_total === null);
}

export function isPortfolioDcaPerformanceResponse(value: unknown): value is { data: PortfolioDcaPerformance } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return isCount(data.bot_count)
    && isCount(data.winning_bot_count)
    && typeof data.total_realized_net === "string"
    && Array.isArray(data.bots)
    && data.bots.every(isBotShare);
}

type FixedShare = { coef: bigint; scale: number };

function parseShare(text: string): FixedShare | null {
  if (!SHARE_PATTERN.test(text) || text.length > 256) return null;
  const negative = text.startsWith("-");
  const unsigned = negative ? text.slice(1) : text;
  const [integerPart, fractionalPart = ""] = unsigned.split(".");
  const coef = BigInt(`${integerPart}${fractionalPart}`);
  if (negative || coef === 0n) return null;
  return { coef, scale: fractionalPart.length };
}

type RingArc = { botId: string; startMdeg: bigint; sweepMdeg: bigint; color: string };

function ringArcs(bots: PortfolioBotShare[]): { arcs: RingArc[]; drawable: boolean } {
  const parsed = bots.map((bot, index) => ({
    botId: bot.bot_id,
    share: typeof bot.share_of_total === "string" ? parseShare(bot.share_of_total) : null,
    color: RING_PALETTE[index % RING_PALETTE.length],
  }));
  const drawable = parsed.filter((entry) => entry.share !== null);
  if (drawable.length === 0) return { arcs: [], drawable: true };
  const scale = Math.max(...drawable.map((entry) => (entry.share as FixedShare).scale));
  const unit = 10n ** BigInt(scale);
  const scaled = drawable.map((entry) => {
    const share = entry.share as FixedShare;
    return { ...entry, units: share.coef * 10n ** BigInt(scale - share.scale) };
  });
  const positiveSum = scaled.reduce((total, entry) => total + entry.units, 0n);
  if (positiveSum > unit) return { arcs: [], drawable: false };
  let cursor = 0n;
  const arcs = scaled.map((entry) => {
    const sweep = (entry.units * FULL_MDEG) / unit;
    const arc = { botId: entry.botId, startMdeg: cursor, sweepMdeg: sweep, color: entry.color };
    cursor += sweep;
    return arc;
  }).filter((arc) => arc.sweepMdeg > 0n);
  return { arcs, drawable: true };
}

function roundCoordinate(value: number): number {
  return Math.round(value * 1000) / 1000;
}

function polar(mdeg: bigint, radius: number): [number, number] {
  const radians = (Number(mdeg) / 1000) * (Math.PI / 180);
  return [
    roundCoordinate(RING_CENTER + radius * Math.cos(radians)),
    roundCoordinate(RING_CENTER + radius * Math.sin(radians)),
  ];
}

function arcPath(startMdeg: bigint, sweepMdeg: bigint): string {
  const endMdeg = startMdeg + sweepMdeg;
  const [outerX1, outerY1] = polar(startMdeg, RING_OUTER);
  const [outerX2, outerY2] = polar(endMdeg, RING_OUTER);
  const [innerX2, innerY2] = polar(endMdeg, RING_INNER);
  const [innerX1, innerY1] = polar(startMdeg, RING_INNER);
  const large = sweepMdeg > FULL_MDEG / 2n ? 1 : 0;
  return `M ${outerX1} ${outerY1} A ${RING_OUTER} ${RING_OUTER} 0 ${large} 1 ${outerX2} ${outerY2} L ${innerX2} ${innerY2} A ${RING_INNER} ${RING_INNER} 0 ${large} 0 ${innerX1} ${innerY1} Z`;
}

type PortfolioPanelProps = {
  data: PortfolioDcaPerformance | null;
  busy: boolean;
  error: string;
  onRefresh: () => void;
};

export function PortfolioPanel({ data, busy, error, onRefresh }: PortfolioPanelProps) {
  const ring = data === null ? { arcs: [], drawable: true } : ringArcs(data.bots);
  const undrawn = data === null ? 0 : data.bots.length - ring.arcs.length;
  return <section className="panel portfolio-panel" aria-labelledby="portfolio-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">LAB · PORTFÖY ÖZETİ · TESTNET</p>
        <h2 id="portfolio-title">Portföy halkası</h2>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={onRefresh}>
        {busy ? "Okunuyor…" : "Yenile"}
      </button>
    </div>
    {error && <div className="form-error" role="alert">{error}</div>}
    {data === null && !busy && !error && (
      <div className="empty-state" role="status">Portföy okunamadı — testnet oturumu yok ya da bağlantı kurulamadı.</div>
    )}
    {data !== null && (
      <>
        <dl className="preflight-facts">
          <div><dt>Bot</dt><dd>{data.bot_count}</dd></div>
          <div><dt>Kazançlı bot</dt><dd>{data.winning_bot_count}</dd></div>
          <div><dt>Toplam net</dt><dd>{data.total_realized_net}</dd></div>
        </dl>
        {data.bots.length === 0 && (
          <div className="empty-state" role="status">Bot-bağlantılı oturum yok — halka çizilemez (botsuz oturumlar toplama girer, halkaya girmez).</div>
        )}
        {data.bots.length > 0 && !ring.drawable && (
          <div className="empty-state" role="status">Pozitif-pay toplamı 1’i aştığı için halka çizilemedi (kayıplı botlar var) — tablo tamdır.</div>
        )}
        {data.bots.length > 0 && ring.drawable && (
          <svg className="portfolio-ring" viewBox="0 0 200 200" role="img" aria-label={`${data.bot_count} bot, toplam net ${data.total_realized_net}`}>
            <circle cx={RING_CENTER} cy={RING_CENTER} r={(RING_OUTER + RING_INNER) / 2} fill="none" stroke="var(--color-border)" strokeWidth={RING_OUTER - RING_INNER} className="portfolio-ring-track" />
            {ring.arcs.map((arc) => arc.sweepMdeg === FULL_MDEG ? (
              <circle key={arc.botId} cx={RING_CENTER} cy={RING_CENTER} r={(RING_OUTER + RING_INNER) / 2} fill="none" stroke={arc.color} strokeWidth={RING_OUTER - RING_INNER}>
                <title>{arc.botId}</title>
              </circle>
            ) : (
              <path key={arc.botId} d={arcPath(arc.startMdeg - 90000n, arc.sweepMdeg)} fill={arc.color}>
                <title>{arc.botId}</title>
              </path>
            ))}
          </svg>
        )}
        {data.bots.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead><tr><th scope="col">Bot</th><th scope="col">Net</th><th scope="col">Pay</th></tr></thead>
              <tbody>
                {data.bots.map((bot, index) => (
                  <tr key={bot.bot_id}>
                    <td><span className="portfolio-swatch" style={{ backgroundColor: RING_PALETTE[index % RING_PALETTE.length] }} aria-hidden="true" />{bot.bot_id}</td>
                    <td><code>{bot.realized_net}</code></td>
                    <td><code>{bot.share_of_total ?? "—"}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {undrawn > 0 && ring.drawable && (
          <p className="helper-text" role="status">{undrawn} bot halka-dışı (negatif/sıfır/tanımsız pay) — değerler tabloda aynen.</p>
        )}
      </>
    )}
    <p className="paper-note">Pay/oran/toplam sunucuda exact-Fraction ile hesaplı; halka yalnız pozitif payları çizer, boşluk uydurulmaz.</p>
  </section>;
}
