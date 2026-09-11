# P1.04.e — Offline tarihsel simülasyon başlatma kanıtı

## Kapsam

Bu alt faz, güncel VERIFIED dataset preflight + aktif offline config hazır olduğunda kullanıcıya strict bir onay adımı üzerinden sınırlı tarihsel OHLCV simülasyonu başlatma davranışını ekler. Sonuç grafiği, işlem tablosu, kalıcı koşu kaydı, ağ emri ve credential kapsam dışıdır.

## Uygulanan sözleşme

- `src/dcabot/application/historical_simulation.py`: `historical_ohlcv_v1`, en fazla 1.000 kapalı bar, ilk bar base açılışı, sonraki barlarda önceden aktif safety/TP adayları, en fazla bir action/bar.
- Safety ve TP aynı bar aralığında erişilebiliyorsa OHLC içi sıra çıkarılmaz; ilgili bar commit edilmeden `INDETERMINATE / AMBIGUOUS_OHLC_PATH` döner.
- Fee/slippage mevcut config’ten exact core sınırında uygulanır; funding `NOT_MODELED`, exchange mark `NOT_AVAILABLE`, forced close yoktur.
- `POST /api/historical-runs/simulate` yalnız current VERIFIED artifact + active offline config revision’larını kullanır, response `persisted=false` taşır ve path/URL/credential içermez.
- UI yalnız run-plan hazırsa `OFFLINE / TARİHSEL / SIMULATED` kapsamını ve accessible confirmation adımını gösterir. Completed, indeterminate ve güvenli hata durumları ayrıdır.

## Kanıt komutları

```powershell
& '.venv\Scripts\python.exe' tools/run_checks.py
cd frontend
npm run build
```

Sonuç: Python `Ran 80 tests ... OK`; frontend TypeScript/Vite build PASS.

## Browser/local kanıtı

- Local API: `127.0.0.1:8000`; frontend: `127.0.0.1:5173`.
- VERIFIED gerçek artifact ile masaüstü DOM akışı: preflight READY → simulation action görünür → confirmation dialog → Escape ile kapanma ve focus dönüşü → Başlat.
- Gerçek artifact + mevcut `config/paper.json` çalıştırmasında HTTP 422 ve güvenli `REDUCER_POLICY_REJECTED` mesajı görüldü. Bu, `base_qty=1` ve `max_entry_notional=1000` değerlerinin gerçek BTC fiyatlı artifact ile uyumsuz olduğunu gösterir; config değiştirilmedi ve ekonomik sonuç uydurulmadı.
- Browser console’da error/warning yok; masaüstü `scrollWidth=1265`, viewport `1280`, yatay taşma yok. Mobil hedef CSS ile 390px kırılımı korunuyor; çalışma ortamındaki browser yüzeyi viewport’u 1280 olarak sabitlediği için gerçek 390px resize kanıtı alınamadı.

## Sınır / sonraki faz

Bu sonuç yalnız koşunun kabul edildiğini, belirsizliği veya güvenli reddini bildirir. Ayrıntılı `summary` içindeki finansal alanların UI’da gösterimi, grafik, işlem tablosu ve kalıcı run kimliği P1.05/P1.06 kapsamındadır.
