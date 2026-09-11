# P1.06.f — Uyumlu historical profile sonucu

Durum: BACKEND_PROFILE_PASS / UI_RESEARCH_PENDING; bağımsız review: NOT_RUN.

## İncelenen kapsam

P1.06.f araştırma raporu, proje talimatı değil doğrulanacak kanıt olarak incelendi. Hedef davranışın backend kısmı: local app → verified dataset preflight → explicit historical profile → offline historical simulation → save → read-only detail.

## Kontrol → test → farklı kontrol → sonuç

1. Dosya sistemi kontrolü: public cache içinde doğrulanmış BTCUSDT/1h artifact mevcut; ilk bar `93576` USDT/BTC açılış taşıyor.
2. Uyumsuzluk matematik kontrolü: `1 × 93576 = 93576 USDT > 1000 USDT`; mevcut `paper` config’in reddedilmesi doğru.
3. Reducer kod kontrolü: cap, `entry_notional + qty × fill_price > max_entry_notional` koşuluyla uygulanıyor; fee cap’e ikinci kez eklenmiyor.
4. Bağımsız demo config testi: rapordaki `base_qty=0.004`, `safety_qty=0.003`, `safety_count=2`, `qty_step=0.001` örneği gerçek 24 bar artifact üzerinde `COMPLETED` verdi; `entry_notional=374.304 USDT`, 1 action.
5. Backend API zinciri: explicit `historical_demo_btcusdt_1h_v1` run-plan → simulate → geçici dedicated SQLite save → detail tamamlandı.
6. Snapshot kimliği kontrolü: detail’de `profile_id=historical_demo_btcusdt_1h_v1`, `profile_version=1`, `venue_filter_provenance=project_fixture`, `historical_filter_claim=false` görüldü.
7. Fail-closed kontrolü: profil yalnız kayıtlı ID ve beklenen dataset eşleşmesiyle yükleniyor; config dosyası serbest path’ten okunmuyor.
8. Odak backend testleri: `16/16 PASS`.
9. Tam Python regresyonu: `113/113 PASS`.
10. Frontend build: `npm run build` — PASS.
11. Python compile/workspace: PASS.

## Araştırma kararının değerlendirmesi

`config/paper.json` değiştirilmedi. Ayrı `historical_demo_btcusdt_1h_v1` profile kabul edildi. Profilin venue filter alanı `project_fixture` olarak işaretlendi; tarihsel Binance filter uyumluluğu iddiası yapılmıyor. Raporun “cap temeli bilinmiyor” iddiası mevcut reducer koduyla doğrulanmadı ve uygulama sözleşmesi buna göre değiştirilmedi.

Bu backend fazında kullanıcı arayüzüne profile selector bağlanmadı; sessiz otomatik profile seçimi yapılmadı. Profile selector’ın bilgi mimarisi ve mobil davranışı ayrı P1.06.f.2 araştırma/uygulama diliminde ele alındı.

## Sonraki tek iş

Anonim UI/UX araştırma kapısı: `docs/P1.06.f.2_Historical_Profile_Secimi_UI_UX_Arastirma_Promptu.md`. Rapor gelmeden profile selector, otomatik profile geçişi veya yeni warning yerleşimi uygulanmayacak.
