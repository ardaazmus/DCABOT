/**
 * Faz AB.1: qwen kart görünümünde salt-görüntü istatistik kutusu.
 * value sunucu exact-metnidir, aynen yazılır (dönüşüm/kısaltma yok);
 * tanımsız değer çağıran tarafından "" geçirilir, 0 uydurulmaz.
 */
export function StatTile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="tile stat" role="group" aria-label={label}>
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
      {sub !== undefined && sub !== "" && <p className="helper-text">{sub}</p>}
    </div>
  );
}
