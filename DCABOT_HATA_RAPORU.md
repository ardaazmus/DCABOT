# DCABOT — Mantıksal ve Yazılımsal Hata Raporu

**Tarih:** 15 Eylül 2026  
**İnceleyen:** Buffy (Codebuff)  
**Kapsam:** 160+ aktif Python dosyası, 6 SQLite store, FastAPI sunucusu, React/Vite frontend  

---

## 🔴 KRİTİK HATALAR

### 1. `engine.py` — `decision()` Fonksiyonunda Ölü Kod / Tutarsızlık

**Dosya:** `src/dcabot/domain/engine.py` (~satır 161)

```python
# decision() içinde:
elif not s.orders and not s.halted and not s.blockers:
    return ("BASE", c.base_qty)
```

`apply()` → INTENT handler'da (~satır 72):

```python
if s.orders or qty != c.base_qty:
    raise ValueError("One base order per deal, with configured quantity")
```

`State.orders` hiçbir zaman sıfırlanmaz — deal tamamlandığında bile eski emirler dict'te kalır. Dolayısıyla `not s.orders` **hiçbir zaman True olamaz** ve `decision()` bu kolda hiçbir zaman `("BASE", ...)` döndüremez.

**Etki:** Yeni deal başlatılamaz (tek deal tasarımı kasıtlı olabilir). `report()` → `global_new_risk_gate_open` alanı daima `False` kalır; deal tamamlandığında yeni risk kapısı açılmaz.

**Öneri:** `decision()` fonksiyonundaki ölü kolu kaldır veya `report()` docstring'inde tek-deal sınırlamasını açıkça belirt.

**Kısmen ele alındı (2026-09-20):** Karar `docs/KARARLAR.md` CORE01'de belgelendi — tek-deal değişmezi kasıtlı çekirdek sınırıdır, `engine.py` bilerek değişmedi. Üst katmanda `historical_simulation.simulate_historical_ohlcv` artık deal kapanınca taze bir `State` açıp yeni BASE başlatıyor (bkz. STATE.md Faz 2.1b), yani ürün seviyesinde "yeni deal başlatılamaz" etkisi orkestrasyon katmanında giderildi. Ama `engine.py:292-293`'teki `decision()` kolu hâlâ hiçbir zaman tetiklenmiyor (`historical_simulation.py` `decision()`'ı hiç çağırmıyor, kendi INTENT/FILL/ORDER_FINAL adımlarını doğrudan uyguluyor) — kod kendisi hâlâ ölü. Canlı/testnet yürütme yolu bu düzeltmeyi henüz kullanmıyor. Tam KAPALI değil; kalan iş bu düzeltmenin canlı yürütme tarafına taşınması veya `decision()`'ın gerçekten kullanılmasıdır.

---

### 2. api.py — _quality_response() Tutarsız Return Tipi — KAPALI (2026-09-20)

**Dosya:** `src/dcabot/server/api.py` (~satır 544)

```python
def _quality_response(report):
    status_code = 422 if report["status"] == "REJECTED" else 200
    content: dict[str, object] = {"data": report}
    if status_code == 422:
        content.update(_error(...))
    response = JSONResponse(status_code=status_code, content=content)
    if len(response.body) > MAX_QUALITY_RESPONSE_BYTES:
        return _problem(422, ...)
    if status_code == 422:
        return response      # ← JSONResponse döndürülüyor
    return content           # ← dict döndürülüyor! (JSONResponse değil)
```

**Doğrulama sonucu:** Güncel _quality_response() hem 200 hem 422 durumunda JSONResponse döndürüyor ve her iki yanıta da Cache-Control: no-store ekliyor. Bu bulgu kapanmıştır; ek kod değişikliği gerekmiyor.

**Eski etki:** Bu bölüm yalnız önceki davranışın kaydıdır; güncel kod için geçerli değildir.

**Eski öneri:** Her iki durumda JSONResponse döndürülmesi güncel kodda uygulanmıştır.

---

## 🟡 ORTA SEVİYE HATALAR

### 3. `quality.py` — `quote_volume`/`trade_count` Parse Sonuçları Kayıp — KAPALI (2026-09-20)

**Dosya:** `src/dcabot/data_adapters/quality.py` (~satır 200)

```python
_decimal(fields[7], "quote_volume", row_number)    # Sonuç hiçbir yere kaydedilmiyor
_integer(fields[8], "trade_count", row_number)      # Sonuç hiçbir yere kaydedilmiyor
```

**Açıklama:** Binance kline formatındaki `quote_volume` ve `trade_count` alanları doğrulanıyor ama parsed değerler hiçbir yere kaydedilmiyor.

**Etki:** `quote_volume` veya `trade_count` hatalı olsa bile rapor "PASS" döndürebilir (sadece format doğrulanıyor, değer aralığı kontrol edilmiyor).

**Kapanış:** KAPALI. Güncel canonical bar sözleşmesi bu iki alanı ekonomik state'e taşımaz; parser bunları yalnız format/aralık doğrulaması için okur ve geçersiz girdiyi reddeder. Bu, aktif ürün borcu olarak açılmadı; kod değişikliği yok.

---

### 4. `api.py` — Config Dosyası Her İstekte Diskten Okunuyor — KAPALI (2026-09-20)

**Dosya:** `src/dcabot/server/api.py` (~satır 558)

```python
def _load_config(profile_id: str = "paper") -> dict[str, Any]:
    if profile_id == "paper":
        with CONFIG_PATH.open(encoding="utf-8") as handle:
            return json.load(handle)
```

**Açıklama:** Her `/api/preview` isteğinde `config/paper.json` diskten okunuyor. Config dosyası değişmediği sürece bu gereksiz I/O.

**Öneri:** Config dosyasını modül yükleme zamanında bir kez oku ve cache'le. Dosya değişikliği için manuel refresh mekanizması ekle.

**Doğrulama sonucu:** Güncel `_load_config()` (`api.py:899-905`) `_PAPER_CONFIG_CACHE` modül-seviyesi tuple'ında `(mtime_ns, config)` tutuyor; dosya `mtime` değişmediği sürece diskten yeniden okumuyor, değiştiğinde otomatik yenileniyor. Bulgu kapanmıştır; ek kod değişikliği gerekmiyor.

---

### 5. `api.py` — Middleware `content-length < 0` Kontrolü Kısmi

**Dosya:** `src/dcabot/server/api.py` (~satır 649)

```python
if declared_size < 0:
    return _problem(400, "MALFORMED_REQUEST", ...)
```

**Açıklama:** HTTP spec'e göre `Content-Length` negatif olamaz. Bu kontrol technically correct ama `declared_size == 0` durumunda后续 `len(body) > MAX_...` kontrolü devreye girer — bu, gereksiz bir memory allocation yaratıyor.

---

### 6. reconciliation.py — hydrate_event_continuity() State Priority — KABUL EDİLEN FAIL-CLOSED SINIR (2026-09-20)

**Dosya:** `src/dcabot/application/reconciliation.py` (~satır 286)

```python
state_priority = {
    ConnectionState.RECONCILIATION_REQUIRED: 0,
    ConnectionState.STALE: 1,
    ConnectionState.GAP: 2,
    ConnectionState.UNKNOWN: 3,
    ConnectionState.FAILED: 4,      # ← En yüksek priority
}
```

**Doğrulama sonucu:** FAILED en yüksek priority (4) olarak tanımlı; hydration sırasında en kötü durum kazanıyor. Bu, geri dönüşü varsaymak yerine fail-closed davranıştır ve mevcut test test_hydration_keeps_failed_state_over_less_severe_observations ile korunur. Bulgu kapatılmış kabul edilir; kod değişikliği gerekmiyor.

**Kabul edilen sınır:** Testnet reseti veya ağ kesintisi sonrası FAILED gözlem güvenilir senkron iddiasını açmaz; yeni authoritative reconciliation gerekir.

---

### 7. `store.py` — `transact()` Exclusive Create Race Condition

**Dosya:** `src/dcabot/persistence/store.py` (~satır 44)

```python
if config is not None:
    Config.parse(config)
    with path.open("xb"):    # Exclusive create
        pass
# ... sqlite3.connect() — arada race condition
```

**Açıklama:** Dosya `xb` ile oluşturulduktan sonra `sqlite3.connect()` ile yeniden bağlanılıyor. İki işlem arasında一小 race condition var. Local demo için düşük risk.

---

## 🟢 DÜŞÜK SEVİYE / KOD KALİTESİ

### 8. `api.py` — CORS Sadece Vite Dev Portu — KAPALI (2026-09-20)

**Dosya:** `src/dcabot/server/api.py` (~satır 623)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type", "X-Filename"],
)
```

**Açıklama:** Production build farklı portla serve edilirse CORS başarısız olur. 5173 yerine configurable origin veya wildcard kullanılmalı.

**Doğrulama sonucu:** `_cors_origins()` (`api.py:94-100`) artık `DCABOT_CORS_ORIGINS` ortam değişkenini okuyor; boş veya `*` içeren değer güvenli yerel varsayılana (`localhost:5173`/`127.0.0.1:5173`) düşüyor, wildcard asla doğrudan uygulanmıyor. Bulgu kapanmıştır; ek kod değişikliği gerekmiyor.

---

### 9. `api.py` — Global Mutable Singleton State

**Dosya:** `src/dcabot/server/api.py` (~satır 95)

```python
DATASET_CATALOG = PublicDatasetCatalog(DATASET_CACHE_DIR, [BINANCE_BTCUSDT_1H_2025_01_01_DATASET])
DOWNLOAD_JOBS = DownloadJobManager()
HISTORICAL_EXECUTIONS: dict[str, HistoricalRunCapture] = {}
```

**Açıklama:** Modül seviyesinde global mutable state. Multi-worker (`uvicorn --workers N`) durumunda her worker ayrı state'e sahip olur. Local single-worker kullanım için yeterli.

**Kabul edilen sınır:** Bu local ürün akışında uvicorn tek worker çalışır; multi-worker deployment kapsam dışıdır.

---

### 10. `App.tsx` — 30+ `useState` Hook'u (Kod Kalitesi)

**Dosya:** `frontend/src/App.tsx`

Tek component'te 30'dan fazla `useState` hook'u var. Bu, component'in çok karmaşık olduğunu gösteriyor.

**Öneri:** Related state'leri grupla veya `useReducer` / state management kütüphanesi (Zustand/Jotai) kullan. Örneğin: `datasetState`, `simulationState`, `savedRunsState` gibi.

---

## 📊 Genel Değerlendirme Matrisi

| Alan | Durum | Not |
|------|-------|-----|
| **Güvenlik** | ✅ İyi | Credential/secret persist edilmiyor; fail-closed tasarım |
| **Exact Arithmetic** | ✅ İyi | Fraction tabanlı; round-trip precision kontrolleri var |
| **Idempotency** | ✅ İyi | Duplicate batch/execution/event kontrolü tutarlı |
| **Persistence** | ✅ İyi | WAL + FULL synchronous + per-event balanced postings |
| **Test Coverage** | ✅ İyi | 869 test, compileall, workspace, frontend build PASS |
| **API Design** | ⚠️ Orta | Problem Details formatı tutarlı, ama tip tutarsızlıkları var |
| **Multi-worker** | ❌ Zayıf | Global mutable state tek worker ile sınırlı |
| **Dokümantasyon** | ⚠️ Orta | STATE.md kapsamlı ama tek-deal sınırlaması net değil |

---

## 🎯 Öncelikli Düzeltme Önerileri

1. _quality_response(): KAPALI; iki durum da JSONResponse + Cache-Control: no-store.
2. **`decision()`** → KISMEN: historical orkestrasyonu deal restart'ı üst katmanda çözdü (bkz. madde 1), `engine.py`'deki kod hâlâ ölü; canlı yürütme yolu kapsam dışı.
3. **`_load_config()`** → KAPALI; mtime tabanlı cache uygulandı.
4. **CORS** → KAPALI; `DCABOT_CORS_ORIGINS` ile configurable, wildcard güvenli varsayılana düşüyor.
5. **`App.tsx`** → KISMEN: `useReducer` ile dataset/simulation/saved-runs grupları taşındı, kalan `useState` sayısı azaldı ama tam konsolidasyon yapılmadı.

---

## 📝 Proje Güçlü Yönleri

- **Kapsamlı Test Kapsamı:** 869 test, her fazda RED→GREEN döngüsü
- **Fail-Closed Tasarım:** Bilinmeyen veri durumları her zaman reddediliyor
- **Exact Financial Arithmetic:** Fraction tabanlı; kesin round-trip dönüşüm kontrolü
- **İdempotent Persistence:** Duplicate batch/execution ID koruması
- **Güvenli Credential Sınırı:** Credential material hiçbir zaman persist edilmiyor
- **Kanıt Kapısı:** Her iddia için TASK + kanıt + bağımsız kontrol döngüsü

---

*Bu rapor 869 testin PASS durumu, compileall/workspace/frontend build PASS ve mevcut kanıt dosyaları doğrultusunda hazırlanmıştır.*
