# P1.04.a — Verified canonical historical input sonucu

## Durum

`COMPLETE / LOCAL_PASS`; bağımsız review `NOT_RUN`.

## Kapsam

Verified katalog seçimini salt-okunur application use case’ine bağladım. Bu küçük dilim yalnız seçilmiş ve daha önce cache bütünlük doğrulamasından geçmiş artifact’ı okur; network, dosya yazımı, credential, backtest yürütmesi, DCA ekonomik hesabı, emir ve testnet yoktur.

## Uygulanan sözleşme

- `PublicDatasetSelection` yalnız `VERIFIED` ve okunabilir artifact olarak kabul edilir.
- Header’sız Binance kline satırları 12 kolonlu raw şemadan `CanonicalBar` tuple’ına çevrilir.
- OHLCV değerleri float kullanılmadan exact decimal string olarak normalize edilir.
- `open_time_us` / `close_time_us` integer microseconds’tır; metadata timezone `UTC` olarak taşınır.
- Source ID, dataset kimliği/dönemi ve artifact SHA-256/byte metadata’sı input’a bağlıdır; path, URL ve credential alanı yoktur.
- Ham kolon sayısı, malformed numeric/integer değerler, ignore alanı, OHLC sınırı, dönem sınırı, artan benzersiz zaman sırası, çakışan bar aralıkları ve `MAX_BARS=100000` sınırı doğrulanır.
- Input immutable dataclass’lar ve tuple bar koleksiyonu olarak döner.

## Değişen dosyalar

- `src/dcabot/data_adapters/historical.py`: bounded raw-kline parser ve canonical input modelleri.
- `src/dcabot/application/historical.py`: verified dataset application use case sınırı.
- `tests/data/test_historical_input.py`: catalog selection → exact canonical input sözleşme testi.
- `TASK.md`, `STATE.md`, `README.md`, `docs/MIMARI.md`, `docs/VERI_VE_SIMULASYON.md`, `docs/OZELLIK_MATRISI.md`: aktif durum ve mimari kayıtları.

## Kanıt

- TDD RED: production module yokken `ModuleNotFoundError: dcabot.application.historical` görüldü.
- Hedef test GREEN: `test_verified_selection_becomes_exact_canonical_bars_with_source_time_metadata` PASS.
- Gerçek local artifact smoke: `bars=24`, `symbol=BTCUSDT`, `timestamp_unit=microseconds`, ilk open `1735689600000000`, son close `1735775999999999`.
- Input nesnesi path/URL taşımadığı için application sınırında local filesystem ayrıntısı çoğaltılmadı.

## Kontroller

- `tools/run_checks.py` — 70/70 PASS.
- `compileall -q src tests` — PASS.
- `tools/check_workspace.py` — PASS.

## Sınırlar / açık kapılar

- Bu parser mevcut explicit raw Binance kline sözleşmesini kapsar; başka kaynak/schema desteği eklenmedi.
- Gap kalitesi ve dataset completeness raporu quality katmanının sorumluluğunda; bu use case sessiz interpolate etmez ve eksik bar üretmez.
- Tarihsel input henüz DCA/backtest reducer’ına bağlanmadı.
- Sıradaki `P1.04.b` UI preflight özeti olacaktır; yeni ekran düzeni kararı öncesinde anonim görsel araştırma kullanıcıdan istenecektir.
