# P1.12.e — Isolated margin ve venue profile karar kapısı

## Durum

`DEFERRED / NO-GO / LOCAL_PASS`; bu mikro fazda production kodu değişmedi.

## Local gerçeklik

Mevcut CORE01 `leverage` ve `initial_equity` alanlarını öğretici/local initial-margin estimate ve sentetik başlangıç varsayımı için kullanır. Bu alanlar venue margin balance, available margin, collateral wallet, maintenance margin veya liquidation authority değildir. Mevcut `liquidation_long` fonksiyonu da açıkça toy/teaching modeldir.

P1.12 araştırması margin alanlarını birbirinden ayırıyor: wallet balance, equity, margin balance, available margin, position margin, order margin, initial margin ve maintenance margin aynı sayı değildir. Isolated pozisyon bazlı, cross hesap bazlı çalışır; MMR risk tier ve ürün/profile sürümüne göre değişir. Liquidation generic futures fill veya tek bir ortak reducer olarak modellenemez.

## Uygulama kararı

Isolated/cross margin state’i, venue liquidation formülü, MMR/bracket/deduction hesabı, collateral dönüşümü veya margin UI/API alanları eklenmedi. Seçilmiş versioned venue profile, risk-tier girdileri, mark authority, fee/funding/close maliyetleri ve bağımsız oracle olmadan herhangi bir numeric margin/liquidation sonucu güvenli değildir.

## Kanıt zinciri

- Araştırma: `docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md`; `CLM-112-05` margin `DEFER`, `CLM-112-06` liquidation `BLOCKED/DEFER`.
- Local inspection: `src/dcabot/domain/config.py`, `src/dcabot/domain/engine.py`, `src/dcabot/domain/math.py`, `docs/MATEMATIK.md`, `docs/CEKIRDEK_KULLANIM.md`.
- Mevcut son kod regresyonu: `uv run --frozen python tools/run_checks.py` → `251/251 PASS`.
- Workspace: `uv run --frozen python tools/check_workspace.py` → `PASS`; `106` aktif Python dosyası.
- Bağımsız karar kontrolü: same formula cannot safely serve isolated and cross because collateral scope and risk authority differ; numeric implementation yapılmadı.

## Yeniden açma koşulları

Bir margin profile ancak seçilen venue/product/mode/version için resmi kaynak kartları, exact field/unit/rounding owner, mark/index authority, risk-tier/bracket verisi, isolated ve cross state-machine’i, positive/negative/edge oracle’ları ve restart/replay kanıtı hazır olduğunda açılabilir. Generic `FUTURES` veya `leverage × notional` varsayımı kabul edilmeyecek.

## Sonraki tek iş

`P1.13.a` — spot grid ailesi için ayrı state-machine, inventory/fee ve level-generation karar kapısı. P1.12 margin/liquidation profile kapısı açık ve devre dışıdır.
