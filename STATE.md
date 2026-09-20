# Durum — 2026-09-20

Aktif faz: **Faz 2 (P1 kapanışı) tamamen kapandı ve `p1-demo-complete` etiketlendi.** Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 880/880 PASS (0 skip); frontend tsc -b temiz, vitest 23/23 PASS.
Eksenler: implementation=DONE(P1) · verification=PASS · evidence_scope=LOCAL_INTEGRATION+CLEAN_CLONE · review=APPROVED_WITH_FINDINGS · deployment=NOT_DEPLOYED

## P1 kapanış ölçütü — bu oturumda tamamlandı (bkz. docs/KARARLAR.md)
1. **Temiz klon + 9 adım:** gerçek `git clone` (kalıcı git config değişikliği yok, yalnız süreç-bazlı `GIT_CONFIG_*` env override), README komutlarıyla backend+frontend ayağa kaldırıldı, 9 adım (veri indir/doğrula → kalite → bot kur → önizle → koş → grafikten incele → kaydet → kapat/aç → reproduce) tarayıcıda canlı doğrulandı (`reproduced=true`, 3 hash eşleşti).
2. **Bağımsız review:** Codex/muse (farklı ajan, salt-okunur, tek dosya çıktı izniyle) `git diff main...HEAD`'i üç katmanlı (kritik/ekonomik → API → frontend) inceledi. Sonuç `APPROVED_WITH_FINDINGS`, rapor: `evidence/P1_CLOSURE_INDEPENDENT_REVIEW_2026_09_20/SONUC.md`. Katman 1-2'de davranışsal kusur yok; 1 LOW + 4 INFO bulgu.
3. **Tek eyleme dönüşen bulgu (F1) Claude tarafından düzeltildi:** `DatasetCatalogPanel.tsx` aksiyon satırının `onClick`'ine, `onKeyDown`'daki hedef-koruma deseninin aynısı (`onRowClick`, `event.target !== event.currentTarget`) eklendi — Kopyala butonuna tıklamak artık satırı seçmiyor. Yeni test eklendi, canlı DOM'da doğrulandı (Copy → `aria-pressed=false`, satır → `aria-pressed=true`).
4. **`git tag p1-demo-complete` atıldı.**

## Faz 2.5 — Stress modeli (önceki tur, Claude yaptı, delege edilmedi)
Tam stress ekonomik modeli (spread/latency/queue/reserve) `DEFERRED/NO-GO` kaldı (P1.16.i.b'nin kendi bağımsız kontrolünde iki çelişki + reserve invariant ihlali). Bunun yerine yalnız mevcut exact `config.slippage` ile ikinci bir profil eklendi (`historical_demo_btcusdt_1h_stress_slippage_v1`, slippage=0.002), yeni ekonomik kod yok. Frontend'e dokunulmadı (mevcut profil seçici + compare ekranı yeterliydi).

## Ajanlar arası işbölümü — genişletilmiş kullanım
Bu oturumda ilk kez Codex/muse **kod yazmak için değil, bağımsız inceleme için** kullanıldı (salt-okunur, tek rapor dosyası izniyle). Sonuç: disiplinli, kanıt-temelli bir rapor — kendi çalıştırdığı komutların gerçek çıktısını verdi, okumadığı alanları `NOT_VERIFIED` bıraktı, tek gerçek bulguyu (F1) doğru şiddet seviyesiyle (LOW) sınıflandırdı. Bu kullanım biçimi ileride büyük diff'lerde ikinci göz olarak tekrarlanabilir.

## Kodda mevcut
- Yerel arayüz (FastAPI 127.0.0.1:8000 + React/Vite 5173): veri seti kaydı, public indirme, kalite raporu, OHLC grafik (etkileşimli marker, klavye+mouse tutarlı), doğrulama, sıralı deal + ekonomik metrikler, SQLite kayıt/listesi, reproduce doğrulama, iki-run karşılaştırma, 4 historical profil (paper, demo v1, demo stress-slippage v1, demo fixed-slice v1).
- CLI tools/bot.py: demo, init/replay/status/audit, preview.
- Çekirdek: exact Decimal/Fraction ladder, net TP, drawdown; idempotent SQLite kayıtları.
- P2 salt-okunur Binance testnet sınırı: public, account, user-stream adaptörleri.

## Bilinen sınırlar
- Signed REST/WS emir, mutation ve mainnet: NO-GO. Gerçek reconnect worker ve REST catch-up yok.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; gerçek likidite modeli yok. Tam stress ekonomik modeli NO-GO.
- API tek worker'a bağlı. Python 3.13 zorunlu; uv sync --frozen.
- Bağımsız review kapsam notları (evidence/P1_CLOSURE_INDEPENDENT_REVIEW_2026_09_20/SONUC.md, NOT_VERIFIED listesi): gerçek tarayıcı/testnet davranışı, yeni ~4.5k satırlık futures/grid/order_list persistence modülleri, evidence/docs içerikleri satır satır incelenmedi — Faz 3 öncesi gerekirse ayrıca ele alınabilir.

## Kararlar (2026-09-20, Claude tarafından alındı — bkz. `docs/KARARLAR.md`)
Sıralı deal persistence, Faz 2 dondurma listesi, Faz 2.5 stress NO-GO + dar slippage-profili, Claude/Codex işbölümü (kod + bağımsız review), P1 kapanış ölçütü tamamlandı ve etiketlendi.

## Sıradaki adım
P1 kapandı. Sırada Arda'nın kapsam kararı: Faz 3'e (P2 — gerçek Binance testnet) geçmek. Bu ilk kez projenin gerçek bir dış sisteme (testnet de olsa) bağlanacağı faz olduğu için TASK.md'de açık soru olarak bırakıldı; Claude roadmap sıralamasına karar verir ama bu geçişin zamanlamasını Arda onaylar.
