# P1.05.a — Minimal güvenli tarihsel sonuç özeti kanıtı

## Kapsam

Bu alt faz, mevcut `historical_ohlcv_v1` simülasyon response’unu frontend’de yeni finansal hesap yapmadan read-only sonuç özeti olarak gösterir. Grafik, action/trade table, equity curve, ROI/risk metrikleri ve kalıcı run kaydı bu alt fazın dışındadır.

## Kabul edilen karar

- `COMPLETED` durumda backend’den gelen `realized_net_after_all_costs`, fee ve position status gösterilir.
- Dataset dönemi, işlenen bar sayısı, model, kısa config hash ve kısa artifact hash gösterilir.
- `OPEN_AT_END` nötr açıklamayla gösterilir; unrealized yalnız açık pozisyonda ve backend string’i olarak gösterilir.
- `INDETERMINATE` durumda ekonomik sonuç özeti başarı gibi gösterilmez; belirsizlik açıklaması gösterilir.
- Funding `NOT_MODELED`, mark `NOT_AVAILABLE`, forced close yokluğu ve `persisted=false` görünürdür.
- Frontend `Number`, `parseFloat`, `toFixed` veya finansal toplama/çıkarma yapmaz.
- Path, URL, credential, stack trace ve canlı/testnet emir akışı yoktur.

## Değişen yüzeyler

- `frontend/src/datasetCatalog.ts`: mevcut backend response’unun tam summary tipleri.
- `frontend/src/DatasetCatalogPanel.tsx`: minimal sonuç paneli, güvenli durum ve limitasyon görünümü.
- `frontend/src/styles.css`: sonuç değerleri, metadata ve limitasyonların responsive düzeni.

## Kanıt komutları

```powershell
& '.venv\Scripts\python.exe' tools/run_checks.py
cd frontend
npm run build
```

Sonuç: Python `Ran 80 tests ... OK`; TypeScript/Vite frontend build PASS.

## Local/browser kanıtı

- Local API ve frontend ile mevcut VERIFIED artifact yüklendi; preflight ve run-plan hazırlandı.
- Önceki P1.04.e onay/başlatma akışı korunuyor.
- Gerçek artifact çalıştırması HTTP 422 `REDUCER_POLICY_REJECTED` verdi; mevcut `config/paper.json` gerçek BTC fiyatlı artifact ile `max_entry_notional` politikasını karşılamıyor. UI güvenli hata durumunu gösterdi ve config değiştirilmedi.
- Browser console’da uygulama kaynaklı error/warning yok; masaüstü yatay taşma yok.
- Gerçek 390x844 viewport override ile yatay taşma görülmedi; onay paneli açıldı, Escape ile kapandı ve focus başlatma düğmesine döndü.

## Sonraki sınır

Grafik, action/trade table veya kapsamlı ekonomik dashboard eklenmeden önce yeni anonim görsel/teknik araştırma gerekir. P1.05.a’nın mevcut API response ve finansal gösterim sınırları korunacaktır.
