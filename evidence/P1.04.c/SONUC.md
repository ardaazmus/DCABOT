# P1.04.c — Salt-okunur tarihsel koşu planı

## Durum

- Faz: `COMPLETE / LOCAL_PASS`
- Bağımsız faz incelemesi: `NOT_RUN`
- Tarih: 2026-09-07
- Sonraki tek faz: `P1.04.d`

## Kapsam kararı

Bu küçük fazda yeni görsel araştırma gerekmedi; P1.04.b’de doğrulanmış preflight kartı korundu ve yalnız mevcut kartın içine aktif config bağlamı eklendi. Yeni koşu başlatma aksiyonu, simülasyon, sonuç kaydı ve yeni ekran eklenmedi.

## Gerçekleşen davranış

- `GET /api/datasets/{dataset_id}/run-plan` verified dataset preflight’ini aktif `config/paper.json` ile aynı salt-okunur response’ta birleştirir.
- Application katmanı `Config.parse` ile offline schema 1’i tekrar doğrular.
- Dataset sembolü ile config sembolü eşleşmiyorsa plan oluşturulmaz; güvenli 409 response döner.
- Config’in exact finansal değerleri (`base_qty`, `safety_qty`, `deviation`, `fee_rate`, `slippage`) string olarak taşınır; UI yeni finansal hesap yapmaz.
- Deterministik SHA-256 config hash’i ve `SIMULATED`, `NOT_STARTED`, `read_only` durumları döner.
- API response URL, yerel path, credential veya emir alanı taşımaz ve `Cache-Control: no-store` kullanır.
- UI mevcut preflight kartında `AKTİF DCA CONFIG`, config hash’i ve `Başlatılmadı · salt okunur plan` bilgisini gösterir.

## Değişen dosyalar

- `src/dcabot/application/historical.py`
- `src/dcabot/server/api.py`
- `tests/api/test_dataset_preflight.py`
- `frontend/src/datasetCatalog.ts`
- `frontend/src/App.tsx`
- `frontend/src/DatasetCatalogPanel.tsx`
- `TASK.md`, `STATE.md`, `README.md`
- `docs/MIMARI.md`, `docs/VERI_VE_SIMULASYON.md`, `docs/OZELLIK_MATRISI.md`

## TDD kanıtı

RED aşamasında yeni test beklenen nedenle başarısız oldu:

```text
AttributeError: module 'dcabot.server.api' has no attribute 'get_dataset_run_plan'
```

Minimal application/API/UI değişikliğinden sonra aynı test GREEN oldu.

```text
Ran 72 tests in 0.461s
OK
```

Ek kontroller:

- `npm run build`: `tsc -b` ve `vite build` başarılı.
- `python -m compileall -q src tools tests`: başarılı.
- `tools/check_workspace.py`: `PASS`, `active_python_files=40`, `backup_layout=EMPTY_OR_NOT_PLACED`.

## Browser/IAB QA

Yerel frontend `http://127.0.0.1:5175/`, API `127.0.0.1:8000` üzerinden test edildi.

Desktop doğrulamasında `AKTİF DCA CONFIG`, `offline · SIMULATED`, `Config hash`, `Başlatılmadı · salt okunur plan` ve gerçek dataset preflight alanları DOM’da görüldü. `Koşuyu başlat`, URL/path, `Traceback` ve `ExceptionType` metni yoktu. `scrollWidth == clientWidth`; console error/warning yoktu.

390px mobil doğrulamasında aynı alanlar görüldü; `scrollWidth=375`, `clientWidth=375` ile yatay taşma yoktu. Dataset seçme etkileşimi sonrası plan özeti korundu ve koşu başlatılmadı.

Bu fazda gerçek tarihsel simülasyon, run sonucu, kalıcı kayıt, grafik ve testnet/live bağlantısı özellikle kapsam dışıdır.
