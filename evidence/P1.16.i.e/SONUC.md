# P1.16.i.e — Minimum dikey uygulama ve dış yüzey karar kapısı

## Nihai karar

- Alt faz durumu: `COMPLETE_WITH_LIMITATION / NO-GO`
- P1.16.i ekonomik stress runner: `DEFERRED / NO-GO`
- Yeni ekonomik kod: `YAZILMADI`
- Yeni persistence schema/adapter: `YAZILMADI`
- Yeni API/UI dış yüzeyi: `YAZILMADI`
- Production readiness: `NO`
- Sonraki tek iş: `P1.17.a` public read-only data authority inventory

P1.16.i.a–d sıralı denetimleri tamamlandı. Raporun bir bölümü yararlı araştırma hipotezleri sağladı; ancak ekonomik stress runner için gerekli tekil authority, sayısal contract, scenario identity, branch isolation, reserve lifecycle ve persistence/recovery kanıtı kapanmadı. Bu nedenle “minimum” görünen bir spread/slippage veya scenario sonucu bile ekonomik iddia üretir ve güvenli dikey dilim sayılamaz.

## Karar gerekçesi: minimum dilim neden açılmadı?

| Önkoşul | Kanıt durumu | Sonuç |
|---|---|---|
| Mevcut ekonomik hesap authority’si ile uyum | Proje core’u exact `Fraction`/`Q`, quote asset `USDT` ve mevcut fee/rounding contract’ına sahip; dış rapor `Decimal + ROUND_UP` öneriyor | Yeni hesap formülü sessizce seçilemez |
| Stress fiyat/fee/volume policy’si | Rapor T-07’de sayısal çelişki taşıyor; volume/latency calibration yok; fee policy mevcut core ile aynı değil | Fill economics açılamaz |
| OHLC scenario identity | Mevcut lineage metadata’dır; bar/order/scenario/seed kimliği yok | Branch sonucu yayınlanamaz |
| Reserve lifecycle | Raporun kendi oracle’ı `create(50) → consume(30) → release(30)` ile negatif available üretiyor | Reserve adapter yazılamaz |
| Atomic persistence/recovery | Base Store ve HistoricalRunStore ayrı sahipler; stress event/branch ve ortak transaction yok | Economic stress sonucu kalıcılaştırılamaz |
| Independent oracle/property tests | Base sınırlar için test var; stress economic alanlarının bağımsız oracle’ı yok | ACCEPT gate oluşmaz |

## Denetim zinciri

1. `P1.16.i.b` araştırma audit’i T-07/T-12 ve reserve karşı örneğini RED olarak kaydetti.
2. `P1.16.i.c` mevcut base/stress metadata identity’sini doğruladı; ekonomik scenario/seed identity’yi kanıtlamadı.
3. `P1.16.i.d` base Store transaction/replay/rollback ve historical snapshot checksum/idempotency sınırlarını doğruladı; stress event, branch isolation, cross-store atomicity ve economic recovery’yi kanıtlamadı.
4. Bu kapıda ayrıca mevcut source yüzeyinde yalnız `stress_lineage.py` ve ilgili testlerin bulunduğu, stress runner/scenario/branch ekonomik implementation’ının bulunmadığı kontrol edildi.
5. Önceki sonuçlar aynı eksik authority’ye işaret ettiği için yeni bir “geçici” ekonomik implementasyon yapılmadı.

## Güvenle korunabilecek mevcut davranışlar

- Mevcut base historical simulation, `INDETERMINATE`/ambiguous durumda kanıtsız ekonomik fill üretmiyor.
- Mevcut `StressLineage`, base result üzerine yazmadan ayrı metadata identity üretir; ekonomik stress sonucu iddiası taşımaz.
- Mevcut base `Store`, kendi local transaction/replay/posting kapsamı içinde çalışır.
- Mevcut `HistoricalRunStore`, immutable snapshot, checksum, source-execution idempotency/conflict ve corruption isolation sınırlarını korur.
- Bu davranışların hiçbiri stress ekonomik modeli olarak yeniden adlandırılmayacaktır.

## Plan kararı

P1.16.i ekonomik stress sonucu üretme kapısı kapalı tutulur. Bu, P1 historical demo akışındaki mevcut doğrulanmış base sonucu geri almaz; yalnız stress/spread/slippage/latency/volume/branch/explicit-reserve kapsamını kanıt gelene kadar erteler. P1.16.i için yeni dış araştırma istenmedi; mevcut rapor ve yerel kontrollerdeki blocker’lar uygulama kararını değiştirecek biçimde zaten kanıtlandı.

Sıradaki uygun P1 işi `P1.17.a` olacaktır: public read-only fiyat/veri authority’sinin mevcut kod ve kapsam envanteri. Bu fazda private credential, gerçek emir veya ekonomik stress runner açılmayacak; önce public feed, stale/gap/reconnect, offline fallback ve simulated-adapter sınırları yerel kanıtla ayrıştırılacaktır.

## Kapanış kontrolleri

- `uv run --frozen python tools/run_checks.py` → `325/325 PASS`.
- `uv run --frozen python tools/check_workspace.py` → `PASS`; `138` aktif Python dosyası.
- P1.16.i.b, `.c`, `.d` evidence kayıtları incelendi; aynı no-go zinciri tutarlı.
- Kod, schema, API ve UI değişikliği: yok.
- Production readiness: `NO`.
