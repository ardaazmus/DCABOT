# P1.05.c.1 — Bounded canonical chart data contract kanıtı

## Kapsam

Bu alt faz yalnız verified canonical kapalı barlardan türetilen, salt-okunur ve bounded grafik veri sözleşmesini ekler. Grafik render'ı, action marker UI'ı, chart library seçimi ve kapsamlı ekonomik görünüm P1.05.c.2/c.3 kapsamına bırakılmıştır.

Kullanıcının sağladığı anonim P1.05.c araştırma raporu araştırma girdisi olarak değerlendirildi; proje talimatı sayılmadı.

## Araştırma kararı

- **ACCEPT:** c.1'in contract-only kalması; ayrı read-only chart DTO/endpoint; marker için ileride `bar_index` birincil anahtar ve `open_time_us` ikincil tutarlılık metadatası; `INDETERMINATE`/`AMBIGUOUS_OHLC_PATH` durumunda grafik ve marker gizleme; 320px sınırı; OHLC değerlerinin string taşınması.
- **SIMPLIFY:** Araştırma raporundaki `/historical-runs/{id}/chart` önerisi, mevcut sistemde kalıcı `run_id` ve historical-run persistence bulunmadığı için dataset-scoped `GET /api/datasets/{dataset_id}/chart-data` olarak uygulandı. `volume` ve `is_closed` c.1 için gerekli olmadığı için eklenmedi.
- **DEFER:** Grafik UI'ı, marker UI'ı, chart dependency, kısmi belirsizlik öncesi görünüm, intrabar zaman/sıra ve ekonomik detay.
- **REJECT:** Mevcut simulation response'unu genişletme, frontend'in chart verisi türetmesi, frontend finansal hesap yapması, c.1'de yeni grafik bağımlılığı ve kalıcı koşu kimliği uydurma.

## Uygulanan sözleşme

- Endpoint: `GET /api/datasets/{dataset_id}/chart-data`.
- Veri yalnız mevcut verified dataset preflight akışından alınır; yeni veri kaynağı, network, credential veya emir yolu açılmaz.
- Response DTO strict ve frozen Pydantic modelleriyle tanımlıdır; bilinmeyen alanlar reddedilir.
- Metadata: `dataset_id`, `artifact_sha256`, `model_id`, `period_start`, `period_end`, `processed_bar_count`.
- Her bar: 1-based `bar_index`, integer `open_time_us`, `close_time_us`, exact `open/high/low/close` stringleri.
- Üst sınır mevcut tarihsel simülasyon sınırıyla aynıdır: en fazla 1.000 bar.
- Oversized kapsam `409 CHART_SCOPE_NOT_ADMISSIBLE` ile fail-closed reddedilir.
- Response `Cache-Control: no-store` taşır ve path bilgisi taşımaz.
- TypeScript tarafında yalnız contract tipi eklendi; grafik render edilmedi ve frontend finansal hesap yapmıyor.
- P1.05.b action/trade table sözleşmesi korunmuştur; marker verisi henüz chart response'a eklenmemiştir.

## Değişen yüzeyler

- `src/dcabot/application/chart_data.py`: verified canonical bar projection ve bounded sınır.
- `src/dcabot/server/api.py`: strict/frozen chart response modelleri ve read-only endpoint.
- `frontend/src/datasetCatalog.ts`: TypeScript chart contract tipleri; render yok.
- `tests/api/test_chart_data.py`: exact contract ve oversized scope testleri.
- `TASK.md`, `STATE.md`, `README.md`, `docs/VERI_VE_SIMULASYON.md`, `docs/MIMARI.md`, `docs/OZELLIK_MATRISI.md`: faz ve kapsam kanıtı.

## Doğrulama

- Odak chart testleri: **2/2 PASS**.
- Tam Python regresyonu: **82/82 PASS** (`tools/run_checks.py`).
- Frontend TypeScript/Vite build: **PASS**.
- Test edilen güvenlik sınırları: `no-store`, exact OHLC stringleri, 1.001 bar için 409 fail-closed ve response'ta path bulunmaması.
- Grafik, marker, canlı borsa, credential, emir ve kalıcı historical-run davranışı bu alt fazda **NOT_RUN / kapsam dışı**dır.

## Kalan sınır ve sonraki iş

Mevcut aktif config gerçek artifact fiyat ölçeğiyle uyumlu olmadığı için önceki canlı simulation smoke'u güvenli `422 REDUCER_POLICY_REJECTED` ile sonuçlanmıştır; config değiştirilmemiştir. Bu durum chart contract testlerini etkilemez.

Sıradaki tek iş `P1.05.c.2`dir. Grafik kütüphanesi, statik render, responsive davranış ve belirsizlik görünümü için yeni anonim görsel/teknik araştırma kapısı açılmadan chart veya marker UI kodu yazılmayacaktır.
