# F15.5 kanıt — DCABOT-native rozetler (15.4 görsel kabul)

## Referans
Yok (DCABOT-native güven sinyalleri, §5). Aynı görsel dilde rozet:
`Badge.tsx` (ok/warn/neutral/closed tonları).

## Yeni ekran
`evidence/F15.5/deal-replay-badge.png` (deal f15shot5: RUNNING +
"Replay Doğrulandı ✓", gerçek replay sonrası).
`evidence/F15.5/futures-exact-badge.png` (merdiven özetinde
"Exact ✓" + tooltip: kesirli aritmetik).
UNKNOWN sarı rozeti birim testte (`badge-warn`); canlı UNKNOWN
verisi bu turda üretilemedi.

## Dürüst fark notu
Rozet yalnız doğrulanmış durumu gösterir: replay rozeti yalnız
`isDealReplayView` geçen yanıttan sonra; Exact rozeti backend
exact-text özetlerde. PBO satırı YOK (endpoint yok, UI matematiği
yasak) → DEFERRED. Canary rozeti YOK (endpoint + risk çapası
yok) → DEFERRED. Mutation gate satırı doc gereği atlandı
(Ayarlar'da zaten var).

## Tasarım gerekçesi (Yönerge m.4)
Sahte güven rozeti, rozetsizlikten kötüdür: veri-akışı olmayan
iki rozet bilinçli ertelendi (KARARLAR). UNKNOWN düşerken ham
değer korunur, rozet eklenir (bilgi kaybı yok).
