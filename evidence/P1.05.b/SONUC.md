# P1.05.b — Read-only action/trade table kanıtı

## Kapsam

Bu alt faz, mevcut `POST /api/historical-runs/simulate` response’undaki `actions` alanını kullanıcıya read-only işlem geçmişi olarak gösterir. Grafik, marker, OHLCV bar veri genişletmesi, yeni endpoint, chart dependency, kapsamlı ekonomik detay, frontend finansal hesap ve persistence bu alt fazın dışındadır.

## Araştırma kararı

Kullanıcının sağladığı anonim P1.05.b araştırma raporu araştırma girdisi olarak değerlendirildi; proje talimatı sayılmadı.

- **ACCEPT:** Mevcut `actions` alanıyla tablo; masaüstünde semantik başlıklar; dar ekranda kart/liste reflow; ham backend rolü; fill price, quantity, fee, bar index ve UTC microseconds gösterimi.
- **SIMPLIFY:** `raw_reference` varsayılan görünümden çıkarıldı; insan okunur tarih dönüşümü ve pagination sonraki küçük iyileştirmeye bırakıldı.
- **DEFER:** OHLCV grafik, marker, canonical chart DTO, chart library, equity curve, ekonomik detay genişletmesi, export ve persistence.
- **REJECT:** Yeni endpoint/response bar genişletmesi, frontend PnL/fee/equity hesabı, null’ı sıfıra dönüştürme, `INDETERMINATE` sonucu başarılı tablo gibi gösterme.

## Uygulanan davranış

- Yalnız `COMPLETED` sonuçta action geçmişi görünür.
- Aksiyonlar backend’in mevcut sırasıyla gösterilir; frontend finansal sıralama veya hesap yapmaz.
- `bar_index`, ham `role`, `open_time_us`, `fill_price`, `quantity` ve `fee` aynen gösterilir.
- `raw_reference` P1.05.b’de gösterilmez; fill price ile karışma riski azaltılır.
- `INDETERMINATE` durumda tablo gösterilmez ve mevcut belirsizlik uyarısı korunur.
- `OPEN_AT_END` durumunda tablo gösterilir; sahte exit/forced-close satırı eklenmez.
- Aksiyon listesi boşsa güvenli boş durum metni gösterilir.
- Desktop `<table>`, `<caption>`, `<th scope="col">` kullanır.
- Mobil CSS, 320px hedefinde tabloyu kart/list görünümüne dönüştürür; finansal stringler wrap edilebilir, clip edilmez.
- UI `Number`, `parseFloat`, `toFixed` veya finansal toplama/çıkarma kullanmaz.

## Değişen yüzeyler

- `frontend/src/DatasetCatalogPanel.tsx`: `ActionTable` ve `COMPLETED` sonuç akışına bağlanması.
- `frontend/src/styles.css`: tablo ve 320px responsive kart/list düzeni.
- `TASK.md`, `STATE.md`, `README.md`, `docs/VERI_VE_SIMULASYON.md`, `docs/MIMARI.md`, `docs/OZELLIK_MATRISI.md`: faz durumu ve kapsam kayıtları.

## Kanıt komutları

```powershell
cd frontend
npm run build
```

Sonuç: TypeScript/Vite frontend build PASS.

## Local/browser kanıtı

- Local API `127.0.0.1:8000` ve frontend `127.0.0.1:5174` ile gerçek VERIFIED dataset preflight/run-plan akışı açıldı.
- Onay dialog’u açıldı ve `Başlat` eylemi çalıştırıldı.
- Mevcut `config/paper.json` gerçek BTC artifact ile uyumsuz olduğu için HTTP 422 `REDUCER_POLICY_REJECTED` oluştu; UI bunu güvenli alert olarak gösterdi.
- Bu nedenle canlı artifact üzerinde `COMPLETED` action tablosu görüntülenemedi; başarı sonucu sentetik olarak üretilmedi.
- 320px viewport’ta anlamlı uygulama içeriği gösterildi. Root/body scroll genişliği viewport ile sınırlı kaldı; mevcut ladder tablosunun kendi iç scroll’u sayfa taşması değildir.
- Browser console error/warning yok.

## Kalan risk

- Başarı action tablosu, mevcut aktif config ile gerçek artifact smoke’unda üretilemedi.
- 1.000 aksiyonluk uzun liste için pagination/virtualization uygulanmadı; mevcut bounded 1.000 bar sınırı korunuyor.
- P1.05.c öncesinde grafik/marker araştırması ve canonical chart veri sözleşmesi yoktur.
