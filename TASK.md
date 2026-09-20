# Aktif iş — Faz 2.5: Stress modeli (KAPSAM ARAŞTIRMASI, Claude sahibi)

Hedef (docs/YOL_HARITASI.md): stress testi — spread/slippage/latency/partial fill; reproducible seed; iyimser/kötümser OHLC model farkı. "Yalnız 2.1–2.4 bittikten sonra, sınırlı tek dilim."
Sahip: Claude (kritik/finansal, bkz. AGENTS.md "Ajanlar arası işbölümü"). Codex'e devredilmez.

## Önce netleştirilmesi gerekenler (kod yazmadan)
- `docs/OZELLIK_MATRISI.md` F24 satırı ve P1.16.i.b-e kayıtları zaten şunu tespit etmişti: stress'in araştırma/kimlik kısmı (`P1.16.i.a-e`) `COMPLETE_WITH_LIMITATION`, ama **ekonomik implementation `DEFERRED/NO-GO`** — resmî kaynaklar exact stress oracle sağlamıyor. Bu, sıfırdan yeni bir stokastik model icat etmenin AGENTS.md'nin "kanıt yetersizse riskli ekonomik davranış açılmaz" ilkesini ihlal edeceği anlamına gelir.
- Bu yüzden Faz 2.5'in "sınırlı tek dilim" olması gerçek bir sınırlamadır, öneri değil: yeni rastgele/stokastik ekonomi YOK. Yalnız **var olan, zaten exact olan mekanizmaları** (config.slippage, INDETERMINATE/AMBIGUOUS_OHLC_PATH ambiguity tespiti) kullanan, deterministic, reproducible bir "en iyi/en kötü durum" senaryosu olabilir mi — buna karar vermek bu dilimin kendisi.

## Adımlar
1. `docs/archive/arastirma-promptlari/P1.16.i.b_Stress_Ekonomik_Sozlesme_Arastirma_Promptu.md` ve ilgili `evidence/P1.16.i*/SONUC.md` kayıtlarını oku — hangi stress sözleşmesi/sınır zaten karara bağlanmış, tekrar icat etme.
2. Dar bir kapsam öner (ör. "aynı dataset'i iki deterministic slippage senaryosuyla [config.slippage=0 vs config.slippage=mevcut×N] yan yana çalıştır, sonucu compare ekranında göster" gibi) — yeni RNG/seed YOK, ikisi de zaten var olan `simulate_historical_ohlcv` + `config.slippage` ile.
3. Öneriyi Arda'ya kısa bir karar notu olarak sun (docs/KARARLAR.md tarzı); onay olmadan implementasyona geçme.

## Değişmez sınırlar
- Credential, secret, signed request, emir, mutation ve mainnet yok.
- Yeni stokastik/RNG ekonomik model YOK — yalnız var olan exact mekanizmaların deterministic kombinasyonu.
- `engine.py` çekirdek State/apply/decision değişmez (önceki fazlardaki gibi, orkestrasyon katmanında kal).
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Kod yazılmadan önce kapsam Arda'ya sunulur ve onaylanır.
- Onaylanırsa: test-first, exact aritmetik, tam checker + frontend tsc/vitest.
- Bağımsız inceleme yapılmadı; `review=NOT_RUN` olarak kalır.
