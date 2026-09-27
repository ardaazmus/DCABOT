/* Faz 17 AA.11: grid iskelet-kartı (qwen sec-grid'in DÜRÜST karşılığı).
 * Grid motoru YOKTUR (ayrı BÜYÜK FAZ ya da ürün kararı bekler); bu kart
 * yalnızca yol-haritası notu + mevcut marjin-projeksiyonuna derin-bağlantı
 * sunar. Canvas/hibrit/slider bilinçli YOK. */

type GridSkeletonCardProps = {
  onOpenMargin: () => void;
};

export function GridSkeletonCard({ onOpenMargin }: GridSkeletonCardProps) {
  return <section className="panel grid-skeleton-panel" aria-labelledby="grid-skeleton-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">GRID · YOL HARİTASI</p>
        <h2 id="grid-skeleton-title">Grid (yol haritası)</h2>
      </div>
      <span className="revision">motor yok</span>
    </div>
    <p>Gerçek bir grid motoru bu sürümde yok — emir ızgarası yürütülmez, pozisyon açılmaz. Mevcut olan: salt-okunur marjin projeksiyonu (notional/teminat/rezerv).</p>
    <button className="primary-button" type="button" onClick={onOpenMargin}>
      Marjin projeksiyonunu aç
    </button>
    <p className="paper-note">Canvas ızgara, hibrit-mod ve kaldıraç-kaydırıcısı bu dilimde bilinçli YOK (qwen vitrini kopyalanmadı).</p>
  </section>;
}
