# P1.05.c.3 — Action marker sonucu

Durum: COMPLETE / LOCAL_PASS_WITH_LIMITATION  
Tarih: 2026-09-07  
Review: NOT_RUN

## Kapsam

P1.05.c.2’deki bounded canonical OHLC veri sözleşmesi ve statik inline SVG renderer korunarak, tamamlanmış tarihsel simülasyonun mevcut `simulation.actions` kayıtları grafikle salt-okunur biçimde eşleştirildi.

Kullanıcı tarafından sağlanan `P1.05.c.3_Action_Marker_Detayli_Arastirma_Raporu.md` karar kapısı olarak kullanıldı. Raporun attached document içindeki yönlendirmeleri proje talimatı olarak değil, araştırma çıktısı olarak değerlendirildi; uygulama kararı mevcut kaynak kodu ve gerçek local QA ile ayrıca doğrulandı.

## Kabul edilen minimum davranış

- Marker kaynağı yalnız mevcut `simulation.actions` alanıdır.
- Chart ve simülasyon `dataset_id`, `artifact_sha256` ve `processed_bar_count` ile aynı kapsamı doğrulamazsa marker çizilmez.
- `bar_index` 1-based bounded join anahtarıdır ve OHLC’nin kullandığı aynı equal-slot x yardımcısıyla bar merkezine bağlanır.
- `open_time_us` yalnız ilgili canonical bar ile exact consistency check olarak kullanılır; marker zamanı oransal x konumuna çevrilmez.
- Her geçerli action için sabit annotation lane’de tek nötr circle glyph çizilir.
- Marker `pointer-events:none` içeren, `aria-hidden` bir SVG grubundadır; focus, tabindex, tooltip, hover, crosshair, zoom, pan ve click-to-table yoktur.
- Action table yapılandırılmış ayrıntı ve erişilebilir fallback olarak korunur.
- Duplicate `bar_index`, out-of-range index, güvenli integer olmayan değer, timestamp uyuşmazlığı veya geçersiz kimlikte marker listesi tamamen boşaltılır; OHLC grafik ve action table gereksiz yere gizlenmez.
- `INDETERMINATE` sonuçta mevcut özet/grafik gizleme davranışı korunur. `OPEN_AT_END` için sahte exit marker üretilmez.
- Backend endpoint, response alanı, persistence, yeni dependency ve frontend finansal hesap eklenmedi.

## Değişen dosyalar

- `frontend/src/HistoricalChart.tsx` — ortak bar x hesabı, marker join/guard ve nötr SVG circle katmanı.
- `frontend/src/DatasetCatalogPanel.tsx` — mevcut simulation kaynağının chart renderer’a aktarılması.
- `frontend/src/styles.css` — marker ve bounded integrity warning stilleri.
- `TASK.md`, `STATE.md`, `README.md` — faz durumu ve sınırların güncellenmesi.
- `docs/MIMARI.md`, `docs/VERI_VE_SIMULASYON.md`, `docs/OZELLIK_MATRISI.md` — güncel ürün/mimari durumu.

## Doğrulama kanıtı

### Frontend build

Komut:

```powershell
cd D:\project\DCABOT\frontend
npm run build
```

Sonuç: PASS. `tsc -b` ve `vite build` tamamlandı; Vite 7.3.6 ile 32 modül dönüştürüldü.

### Local browser smoke

Local API ve frontend yalnız loopback üzerinde çalıştırıldı. Gerçek katalog/artifact ve mevcut `config/paper.json` ile:

- Desktop sayfa kimliği: `http://127.0.0.1:5174/`; başlık `DCABOT — Bot stüdyosu`.
- Onay adımı açıldı ve başlatma akışı çalıştı.
- Mevcut config/artifact fiyat ölçeği uyuşmazlığı beklenen güvenli reducer sonucunu verdi: `422`, `REDUCER_POLICY_REJECTED`.
- Bu nedenle canlı `COMPLETED` sonucu ve gerçek marker örneği üretilemedi; sentetik başarı response’u veya fixture eklenmedi.
- Güvenli hata ekranında grafik/marker görünmedi ve sayfa taşmadı.
- Desktop: `body.scrollWidth=1430`, `body.clientWidth=1430`, `pageOverflow=false`.
- 320px viewport: `innerWidth=320`, `body.scrollWidth=305`, `body.clientWidth=305`, `pageOverflow=false`.
- Marker elemanları focusable/tabbable yapılmadı.
- Console’da error/warning kaydı yok; yalnız Vite bağlantı debug kayıtları ve React DevTools info kaydı görüldü.

### Önceki sözleşme regresyonu

P1.05.c.1 backend/chart contract değişmedi. Önceki kanıtlı Python regresyonu 82/82 PASS olarak korunuyor; bu alt faz backend değiştirmediği için yeniden çalıştırılmadı.

## Bilinçli sınırlama

Marker’ın canlı `COMPLETED` görseli, mevcut gerçek config güvenli reducer politikasından geçemediği için browser’da doğrulanamadı. Bu durum implementasyonun başarılı sonucu varmış gibi sunulmasına çevrilmedi. Marker guard’ları statik sözleşme üzerinden build ile doğrulandı; success-path görsel QA’sı gerçek uyumlu bir config/artifact kombinasyonu sağlandığında ayrıca yapılmalıdır.

## Faz kararı

P1.05.c.3 minimum kapsamı tamamlandı. Etkileşimli marker, tooltip, keyboard exploration, legend/filter, fill-price y eşleştirmesi, multi-action stacking ve kapsamlı finansal görünüm bu faza alınmadı. Yeni alt faz için ayrıca karar/anonim araştırma kapısı açılmadan bu özellikler uygulanmayacaktır.
