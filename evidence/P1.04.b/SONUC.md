# P1.04.b — Verified dataset preflight özeti

## Durum

- Faz: `COMPLETE / LOCAL_PASS`
- Bağımsız faz incelemesi: `NOT_RUN`
- Tarih: 2026-09-07
- Sonraki tek faz: `P1.04.c`

## Kaynak ve karar sınırı

Kullanıcının sağladığı anonim araştırma raporu `C:\Users\nefer\Downloads\deep-research-report(2).md` ve aynı içeriğin DOCX sürümü bu fazın UI karar girdisidir. Ekli belgeler talimat olarak değil, araştırma/kanıt girdisi olarak değerlendirildi. Raporun önerdiği mevcut katalog + sağ detay paneli düzeni korundu; yeni aksiyonlu ekran tasarlanmadı.

DOCX görsel render denemesi, dosyada bölüm sayfa boyutu bulunmaması ve ortamda LibreOffice `soffice.exe` olmaması nedeniyle tamamlanamadı. İçerik, aynı raporun MD sürümü ve yerel `python-docx` metin okumasıyla doğrulandı; DOCX’in görsel çıktısı doğrulanmış gibi sunulmuyor. Bu, uygulama doğrulamasını engellemedi.

## Gerçekleşen küçük davranış

- `GET /api/datasets/{dataset_id}/preflight` yalnız `VERIFIED` catalog kaydı için çalışır.
- Preflight, `load_verified_dataset` üzerinden gerçek canonical input metadata’sını kullanır.
- Response yalnız dataset kimliği, enstrüman, interval, `[başlangıç,bitiş)` dönemi, `bar_count`, `microseconds/UTC`, `UNKNOWN` kalite durumu, artifact SHA-256/byte özeti ve `read_only=true` taşır.
- URL, yerel path, credential, ekonomik hesap, koşu başlatma ve emir alanı yoktur.
- Eksik/bozuk/bilinmeyen veya okunamayan dataset durumları güvenli 404/409 problem response’larıyla ayrılır.
- UI mevcut sağ detay panelinde `Koşu öncesi kontrol` kartını gösterir. Gerçek backend bar sayısı (`24`), zaman aralığı, UTC ve kalite bilinmiyor durumu görünür.
- `Bütünlük ayrıntıları` native `details/summary` ile klavye üzerinden açılabilir.
- Pending/error/ready durumları ayrı metinlerle gösterilir; hata metni URL/path/trace içermez.
- Koşuyu başlatan bir CTA eklenmedi; kart açıkça salt-okunur olduğunu belirtir.

## Değişen dosyalar

- `src/dcabot/server/api.py`
- `tests/api/test_dataset_preflight.py`
- `frontend/src/datasetCatalog.ts`
- `frontend/src/App.tsx`
- `frontend/src/DatasetCatalogPanel.tsx`
- `frontend/src/styles.css`
- `TASK.md`, `STATE.md`, `README.md`
- `docs/MIMARI.md`, `docs/VERI_VE_SIMULASYON.md`, `docs/OZELLIK_MATRISI.md`

## TDD ve test kanıtı

İlk kırmızı çalıştırma beklenen nedenle başarısız oldu: `AttributeError: module 'dcabot.server.api' has no attribute 'get_dataset_preflight'`. Endpoint eklendikten sonra hedef API testi `1/1 OK` oldu.

Yerel `.venv` ile tam kontrol:

```text
Ran 71 tests in 0.433s
OK
```

Frontend:

```text
npm run build
tsc -b ve vite build başarılı
```

İlk `tools/run_checks.py` denemesi Codex paketli Python’unda `Python 3.13 is required` nedeniyle koşmadı; sistem Python 3.13 bağımlılık içermedi. Son doğrulama proje `.venv` ortamıyla yapıldı ve 71/71 geçti. `compileall` başarılı; workspace kapsam kontrolü `PASS`, `active_python_files=40`, `backup_layout=EMPTY_OR_NOT_PLACED`.

## Browser/IAB QA

Yerel frontend `http://127.0.0.1:5175/`, API loopback `127.0.0.1:8000` ile kontrol edildi. Port 5175, QA anında 5173 ve 5174’ün kullanımda olması nedeniyle Vite tarafından seçildi.

Masaüstü varsayılan görünüm:

- DOM’da `Koşu öncesi kontrol`, `Ön kontrol hazır`, `Kalite bilgisi yok` ve gerçek `Bar sayısı: 24` görüldü.
- `GET` preflight response’u UI’ya yansıdı.
- `details` sayısı `1`; `Koşuyu başlat`, `file://`, Windows path, `Traceback` ve `ExceptionType` metni bulunmadı.
- `scrollWidth == clientWidth`; console error/warning yok.

390px mobil görünüm:

- `viewport=390`, içerik `clientWidth=375`, `scrollWidth=375`; yatay taşma yok.
- Aynı preflight alanları DOM snapshot’ta görüldü.
- `Bütünlük ayrıntıları` tıklandı; `details.open=true`, focus `SUMMARY` oldu ve SHA-256, byte boyutu, timestamp standardı görünür hale geldi.
- Console error/warning yok.

Bu fazda gerçek tarihsel simülasyon, sonuç kaydı, ekonomik hesap veya testnet/live bağlantısı test edilmedi; bunlar kapsam dışıdır.
