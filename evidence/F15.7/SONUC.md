# F15.7 kanıt — Optimize → sweep bağı (15.4 görsel kabul)

## Referans
`02_pionex_futures_dca.webp` / `03_3commas_grid_bot.webp` (Profit
per Grid + "Optimize" linki). Referanslarda gerçek optimizer yok;
DCABOT 14.5+14.6 ile gerçeğini yapar (§5 ilkesi).

## Yeni ekran
`evidence/F15.7/optimize-applied.png` (canlı tur: "En iyi net:
2.61218064 (6 deneme · 3 atlandı)", deviation 0.01 + take_profit
0.01 forma yazıldı, "Öneri forma yazıldı.").

## Dürüst fark notu
Yeni uç `POST /api/sweeps/optimize` (profil-tabanlı base config,
grid/random sampler, exact Fraction sıralama, 1-32 deneme, seed'li
belirleyici). Tarif-bazında atlama AÇIKÇA raporlanır: bu turda 3
tarif motorun `average_entry_price` exactness tuzağına takıldı
(geçerli config, sonlanmayan ortalama — motor sözleşmesi değişmedi,
Faz 16 adayı). Grid formu Optimize DIŞIDIR (grid sweepable değil).

## Tasarım gerekçesi (Yönerge m.4)
Sweep fail-fast kalır; OPTIMIZE üst-seviye olarak tarifleri tek
tek koşar, koşamayanı koduyla listeler, hiçbiri koşamazsa ilk
hatayı yükseltir (sessiz düşürme yok). Sıralama metriği
`realized_net_after_all_costs` (exact). Arama uzayları statik
exact presetlerdir (UI çarpan matematiği yok).
