# P1.02.a — Yerel CSV/ZIP kalite raporu

Durum: IMPLEMENTED / LOCAL_PASS  
Bağımsız inceleme: NOT_RUN  
Kapsam: yalnızca yerel, salt-okunur CSV/ZIP okuma ve deterministik kalite raporu.

## Teslim

- `src/dcabot/data_adapters/quality.py`: UTF-8 CSV, canonical bar/trade şeması, timestamp, UTC/microseconds bildirimi, OHLCV/trade değer aralıkları, sıra, duplicate, conflict ve gap raporu.
- Tek symbol tutarlılığı ve yalnız kapalı bar kabulü kalite reddi olarak raporlanır.
- ZIP için tek CSV adayı, üye sayısı/açılım boyutu, uzantı, traversal ve symbolic-link reddi.
- `src/dcabot/server/api.py`: `POST /api/data-quality`; başarılı rapor, raporlu 422 ve input boyut sınırı.
- Kalıcı dataset kaydı, alan eşleme ekranı, public indirme, credential ve emir yolu bu faza alınmadı.

## Kanıt

- `uv run --frozen python tools/run_checks.py`: **50 test PASS**.
- `uv run --frozen python tools/check_workspace.py`: **PASS**; yedek alanı taranmadı/çalıştırılmadı.
- Gerçek yerel HTTP `POST http://127.0.0.1:8000/api/data-quality` ile `bars.csv`: **200**, `PASS_WITH_WARNINGS`, `kind=bar`, `row_count=3`, gözlenen gap `1`.
- Gerçek yerel HTTP eksik şema ile: **422**, `status=REJECTED`, `unsupported_schema` raporu.

## Sınır ve sonraki faz

Bu sonuç alan eşleme veya UI kabulü değildir. Sıradaki tek iş `P1.02.b`: kullanıcı seçimi sonrası canonical alan eşleme ve kalite ekranının ilk dikey dilimi. P2 testnet bu P1 zinciri tamamlanmadan başlatılmayacaktır.
