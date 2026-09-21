# F15.3b kanıt — Futures DCA Pionex sırası (15.4 görsel kabul)

## Referans
`docs/referans_ekranlar/02_pionex_futures_dca.webp` (sağ panel sırası:
merdiven → TP → yatırım), `docs/wireframes/15_3b_futures_dca.svg` (ölçü).

## Yeni ekran
`evidence/F15.3b/futures-dca-ladder.png` (gerçek uçlar: özet 4 pay/150 giriş,
marjin 600/ELIGIBLE).

## Dürüst fark notu
Pionex sırası tamam: parite → yön → seviyeler → merdiven+paylar → TP çipleri →
yatırım+kaldıraç → özet. Ancak: (1) merdiven satırları kullanıcı eklemez,
grid hesabından gelir (fiyat uydurulamaz); (2) tahmini liq YOK — venue risk
kademesi gerekir, `isolated_liquidation` API'de değil; (3) kaldıraç sliderı
bilgi amaçlıdır (profil kaldıracı kapıda 1'e sabit); (4) Pionex'in 2/4
numaraları yerine ardışık 1/2/3 kullanıldı (ara numara yok).

## Tasarım gerekçesi (Yönerge m.4)
Pozisyon projektörü keyfi pay ağırlıklarında 422 veriyordu (ara-ortalama
exactness değişmezi) — bu yüzden YENİ uç `POST /api/futures/ladder/summary`
(`ladder_summary.py`, Fraction-exact): toplam her zaman exact, ortalama
sonlanmıyorsa `weighted_average_exact=false` + değer yok (yuvarlama YOK).
Marjin, özet ortalamadan tek konsolide satırla projekte edilir (matematik
yalnız toplamı tüketir; notta açıkça yazar). Sözleşme çarpanı 1'dir
(pay=baz birim tanımı, çifte sayım yok). UI'da toplama/ortalama hesabı yok.

## Doğrulama
- checker 1419/1419 PASS (1 skip, +5 merdiven), tsc temiz, vitest 211/211.
- Ekran görüntüsündeki tüm sayılar gerçek uç yanıtlarıdır (curl ile de doğrulandı).
