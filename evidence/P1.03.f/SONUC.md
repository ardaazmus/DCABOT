# P1.03.f — public download job sonucu

## Kapsam

Mevcut P1.03.b bounded public downloader ve atomik verified cache üzerine, UI’dan sonraki download/progress dikey dilimi için local job sözleşmesi eklendi. Gerçek public indirme bu doğrulama turunda çalıştırılmadı.

## Uygulanan davranış

- Downloader `on_progress` ve `cancel_check` hook’larıyla bounded stream sırasında ilerleme ve iptal bildirir.
- İptal veya doğrulama hatasında staging `.part` dosyası temizlenir; hash/byte/ZIP doğrulanmadan final cache yayımlanmaz.
- `DownloadJobManager` dataset başına tek aktif job tutar.
- Job durumları: `QUEUED`, `RUNNING`, `RETRYING`, `SUCCEEDED`, `FAILED`, `CANCELLED`.
- Retry sayısı bounded’dır; varsayılan manager en fazla 3 deneme kullanır, testte 2 deneme kanıtlandı.
- API endpoint’leri:
  - `POST /api/dataset-downloads`
  - `GET /api/dataset-downloads/{job_id}`
  - `POST /api/dataset-downloads/{job_id}/cancel`
- Start request strict `dataset_id` alır ve yalnız `PublicDatasetCatalog.plan_for()` üzerinden explicit registry planına ulaşır.
- Job response yalnız job ID, dataset ID, durum, deneme, progress, cache hit ve güvenli hata kodu taşır; URL/path/ham exception içermez.
- Job API bellektedir; uygulama yeniden başlatıldığında job geçmişi korunmaz. Kalıcı job/dataset metadata bu fazın dışındadır.

## Uygulanan dosyalar

- `src/dcabot/data_adapters/public_download.py`: progress/cancel hook’ları ve `DownloadCancelled`.
- `src/dcabot/data_adapters/download_jobs.py`: bounded in-memory job manager.
- `src/dcabot/data_adapters/catalog.py`: explicit plan erişimi.
- `src/dcabot/server/api.py`: start/status/cancel endpoint’leri ve path/url içermeyen DTO’lar.
- `tests/data/test_download_jobs.py`: cancellation cleanup, retry, duplicate active job.
- `tests/api/test_dataset_catalog.py`: start/status/cancel DTO ve unknown dataset contract.
- `README.md`, `docs/MIMARI.md`, `docs/VERI_VE_SIMULASYON.md`, `TASK.md`, `STATE.md`.

## Kanıt

- Hedef testler: 9/9 PASS.
- Tam regression: 69/69 PASS.
- `npm run build`: P1.03.e frontend build PASS; bu faz frontend dosyası değiştirmedi.
- Gerçek loopback smoke: `GET /api/datasets=200`, `Cache-Control: no-store`, `count=1`, response’ta path yok; bilinmeyen job `404 DOWNLOAD_JOB_NOT_FOUND`; bilinmeyen dataset download start `404 DATASET_NOT_FOUND`.
- Download job testleri: iptal sonrası `.part` yok; bozuk payload’da iki bounded retry sonrası `FAILED`; aynı dataset için ikinci aktif job reddedildi.
- `tools/check_workspace.py`: önceki P1.03.e kanıtındaki workspace PASS korunuyor; yedek çalıştırılmadı.

## Açık sınırlar

Bu fazda katalog UI’sına progress/cancel/retry kontrolü bağlanmadı; bu P1.03.g’dir. Job durumu persistence içermez. Gerçek public kaynak indirmesi ve internet erişilebilirliği bu turda doğrulanmadı; yalnız fake opener ve loopback API sözleşmesi doğrulandı. Credential, testnet ve live emir yoktur.

Durum: `COMPLETE / LOCAL_PASS`; bağımsız inceleme: `NOT_RUN`.
