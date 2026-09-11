# P1.19.a — Result shell responsive state acceptance

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Production readiness: `NO`  
Tarih: 2026-09-10

## Karar

P1.19.a mevcut result shell için kapatıldı. Kontrol sırasında legacy
`HistoricalSimulationResponse` sözleşmesinin `summary` alanını kullandığı, UI'ın
ise yalnız `final_economic_summary` alanını render ettiği doğrulandı. Bu gerçek
uyumsuzluk minimum frontend fallback'i ile düzeltildi:

```text
economicSummary = final_economic_summary ?? summary ?? null
```

Backend contract, ekonomik hesap ve response authority değiştirilmedi.

## Claim → control → RED → minimum fix → independent control

| Kabul / iddia | İlk kontrol | Sonuç / düzeltme |
|---|---|---|
| Completed regular historical result özeti görünür | Gerçek local profile `historical_demo_btcusdt_1h_v1` çalıştırıldı; status completed iken summary ve explanation görünmüyordu | `RED`: UI yalnız fixed-slice alanını arıyordu. `economicSummary` fallback eklendi |
| Completed result fixed-slice akışı bozulmaz | Aynı ekran fixed-slice profile ile çalıştırıldı | `PASS`: fixed-slice `final_economic_summary` önceliği korunuyor |
| Idle/empty state güvenli ve açık | Profile değişimi sonrası result DOM'u temizlendi; “Hazır · henüz çalıştırılmadı” ve başlatma eylemi göründü | `PASS` |
| Loading state ekonomik sonuç göstermiyor | Simülasyon isteği CDP Fetch interception ile geçici olarak bekletildi | `PASS`: “Simülasyon çalışıyor”, disabled button; summary yok |
| Error state sessizce completed görünmüyor | Simülasyon endpoint'i yalnız local Chrome içinde bloklandı | `PASS`: “Simülasyon başlatılamadı” teknik hata mesajı; summary yok |
| Indeterminate state backend sınırını koruyor | Mevcut API testleri ve UI branch inspection kontrol edildi | `PASS_WITH_LIMITATION`: indeterminate branch yalnız backend `execution_status` ile açılıyor; bu koşuda gerçek UI screenshot akışı çalıştırılmadı |

## Bağımsız sonuçlar

Frontend HMR sonrası legacy completed akışında:

```text
simulation status: completed
historical-result-summary: present
historical-explanation-card count: 5
```

Bu kontrol frontend'in `summary` alanını yeniden hesaplamadığını; backend'in
gönderdiği aynı alanı yalnız alternatif response shape için okuduğunu doğrular.

## Doğrulama

```text
frontend npm run build: PASS
Python regression: 359/359 PASS
Python compileall: PASS
Workspace check: PASS
Idle/empty result state: PASS
Loading result state: PASS
Error result state: PASS
Completed legacy response state: PASS
Completed fixed-slice response state: PASS (önceki P1.18.d akışında)
Indeterminate UI visual flow: NOT_RUN in this slice
```

## Korunan sınırlar

Bu mikro fazda yeni finansal formül, frontend hesaplama, backend response alanı,
network davranışı, persistence, LLM, gerçek emir, testnet veya canlı venue yolu
eklenmedi. Değişiklik yalnız mevcut iki backend response biçiminin UI'da aynı
read-only result shell'e bağlanmasıdır.

```text
IMPLEMENTATION_GATE=COMPLETE_WITH_LIMITATION
BACKEND_CONTRACT_CHANGE=NO
FRONTEND_ECONOMIC_CALCULATION=NO
NETWORK_SCOPE=LOCAL_QA_ONLY
NEXT_SINGLE_WORK=P1.19.b
```
