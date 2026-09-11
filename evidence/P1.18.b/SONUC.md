# P1.18.b — Read-only explanation response binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Kapsam

P1.18.a’da üretilen bounded, rule-based `ReadOnlyExplanation` kayıtları mevcut
tarihsel simulation response modellerine bağlandı. Bu mikro faz yalnız response
sözleşmesini ve frontend tip sınırını kapsar; yeni UI görünümü, LLM, network,
persistence, candidate/order/fill, reserve, balance veya PnL authority eklemez.

## 2. Claim → kontrol → sonuç

### Claim A — Açıklamalar mevcut response’a ekonomik authority eklemeden taşınabilir

Local kontrol: `HistoricalSimulationResponse` ve
`HistoricalFixedSliceSimulationResponse` mevcut authoritative result alanlarını
koruyor; yalnız `explanations` alanı P1.18.a projection’ından okunuyor. API
yardımcısı projection’ı yeniden hesaplamıyor ve response oluştururken yalnız
bounded açıklama alanlarını kopyalıyor.

### Claim B — Sözleşme bounded ve fail-closed kalabilir

`ReadOnlyExplanationResponse` için `extra="forbid"`, `strict=True`, `frozen=True`
ve alan uzunluğu/pattern sınırları uygulandı. `code`, `severity`, `title`,
`message`, `source` ve `context` dışında alan kabul edilmiyor. Frontend yalnız
aynı response biçimini tip olarak tanıyor; finansal hesap yapmıyor.

### Claim C — Persisted run formatı geriye dönük korunabilir

Local call-path kontrolünde persistence, API response DTO’sunu değil mevcut
historical capture/result snapshot’ını yazıyor. `explanations` yalnız API response
katmanında kaldı; kayıtlı run schema’sına eklenmedi. Mevcut persistence testleri
ve historical run reopen akışı regresyonda geçti.

## 3. RED kanıtı

İlk gerçek regresyon çalıştırmasında üç hata görüldü:

1. Response body’de `explanations` alanı yoktu.
2. Fixed-slice result top-level `funding_status` ve `mark_status` taşımadığı için
   projection status okuması başarısız oldu.
3. Aynı fixed-slice status eksikliği focused API testlerinde de görüldü.

Bu RED sonucu, response binding’in ve result-shape uyarlamasının gerçekten eksik
olduğunu gösterdi; varsayımla uygulama kabul edilmedi.

## 4. Minimum düzeltme

- `ReadOnlyExplanationResponse` API DTO’su eklendi.
- Her iki historical response’a bounded `explanations` listesi bağlandı.
- Fixed-slice projection için status kaynağı mevcut summary/model sınırından
  fail-closed biçimde çözüldü; yeni ekonomik alan üretilmedi.
- Frontend’e yalnız `ReadOnlyExplanation` response tipi eklendi; görünüm veya
  hesaplama eklenmedi.
- Historical API testlerinde açıklama kodları, bounded liste ve ekonomik alan
  izolasyonu doğrulandı.

## 5. Bağımsız kontrol ve kalite sonucu

```text
P1.18.b focused response assertions: PASS
Independent economic-field isolation assertion: PASS
tools/run_checks.py: 359/359 PASS
compileall src tests: PASS
tools/check_workspace.py: PASS
frontend npm run build: PASS
active_python_files: 147
```

Bağımsız kontrolde response açıklama kayıtlarının ilk context’inde `pnl`
bulunmadığı ve serialized açıklama item’ında
`realized_net_after_all_costs` taşınmadığı doğrulandı.

## 6. Bilinçli sınırlar

- Açıklamalar henüz frontend’de görsel olarak gösterilmiyor.
- UI finansal veri hesaplamıyor; yeni bir UI bileşeni eklenmedi.
- Dış LLM, öneri, bildirim, paylaşım, network ve canlı transport yok.
- Persistence response’a `explanations` yazmıyor; bu faz persisted schema migration
  değildir.
- P1.17.j’deki public live transport `NO-GO/DEFERRED` kararı değişmedi.

## 7. Karar

```text
IMPLEMENTATION_STATUS=COMPLETE_WITH_LIMITATION
PRODUCTION_READINESS=NO
NEXT_SINGLE_WORK=P1.18.c
NEXT_GATE=UI_UX_RESEARCH_REQUIRED
```

P1.18.c’de açıklamaların hangi ekranda, hangi yoğunlukta ve hangi responsive/
erişilebilirlik davranışıyla gösterileceği araştırılmalıdır. Kullanıcı tarafından
onaylanmış görsel araştırma gelmeden UI görünümü veya yeni ekran uygulanmayacaktır.
