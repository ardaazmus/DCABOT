# P1.16.i.a — Core/store authority ve scenario evidence inventory

## Karar

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Alt faz: `P1.16.i.a` tamamlandı
- Sonraki tek iş: `P1.16.i.b` exact stress economic contract araştırma/karar kapısı
- Anonim araştırma promptu: `docs/archive/arastirma-promptlari/P1.16.i.b_Stress_Ekonomik_Sozlesme_Arastirma_Promptu.md` (2026-09-20'de arşivlendi; içerik/hash değişmedi)
- Production readiness: `NO`

## Kanıtlanan mevcut sahiplik

| Alan | Mevcut yerel authority | Kanıtlanan sınır |
|---|---|---|
| Economic transition | `src/dcabot/domain/engine.py` | `INTENT`, `FILL`, `ORDER_FINAL`, `UNKNOWN`, `MARK`, `FUNDING`; reducer state’i tek ekonomik geçiş sahibidir. |
| Partial/late fill | `engine.py` ve P1.07 testleri | Exact cumulative fill/leaves korunur; late fill `UNKNOWN` ve `LATE_FILL_AFTER_FINAL` blocker’ı üretir. |
| Fee | `engine.py`, `historical_simulation.py`, `persistence/store.py` | Fee quote asset içinde, exact miktar ve mevcut quantum ile hesaplanır/post edilir; stress-specific fee policy yoktur. |
| Slippage | `historical_simulation.py` | Mevcut normal historical modelde fill öncesi tek config slippage uygulanır; ayrı stress profile scenario runner değildir. |
| Volume | `historical_simulation.py` | Bar volume format/negatiflik açısından doğrulanır; fill participation veya volume cap uygulanmaz. |
| Latency/queue | Aktif core ve historical runner | Economic latency, queue position veya delayed order state bulunamadı. |
| OHLC ambiguity | `historical_simulation.py` ve fixed-limit uygulama policy’si | Aynı bar içinde safety/TP reachability çakışması `INDETERMINATE`; genel stress scenario tree/ordering modeli yoktur. |
| Persistence/replay | `src/dcabot/persistence/store.py`, `historical_runs.py` | Economic journal transaction/replay/posting audit ve historical snapshot checksum vardır; stress result/effective-time scenario event owner’ı yoktur. |
| Reserve | P1.07/P1.11 mevcut sınırları | `reserve_model=NONE` veya ayrı reservation persistence sınırı vardır; stress fill için atomic reserve lifecycle kanıtı yoktur. |
| Scenario identity | `stress_lineage.py`, `evaluation_run_binding.py` | Base result’tan ayrı deterministic metadata kimliği ve persisted binding vardır; stress ekonomisi hesaplanmaz. |

## Karşı kontrol sonucu

Mevcut `slippage`, `fee` ve `volume` adlarının bulunması tek başına spread/slippage/latency/volume stress modelinin uygulandığını kanıtlamaz. Kod yolu incelendiğinde volume yalnız dataset validation’da, slippage normal fill fiyatı üretiminde, fee ise mevcut quote-asset posting zincirinde kullanılıyor. Latency/queue participation ve senaryo dallanması için aktif economic transition bulunamadı.

Bu nedenle aşağıdaki davranışlar varsayımla açılmadı:

- spread/slippage’ın hangi fiyat referansına ve hangi sıraya uygulanacağı,
- per-fill fee rounding ile aggregate fee eşitliği,
- bar içi latency/queue/volume participation ve partial fill sırası,
- ambiguous OHLC için scenario seti ve sonuçların karşılaştırılması,
- stress sonucunun reserve, persistence, replay ve API/UI ile bağlanması.

## Kontroller

- Aktif domain, historical runner, fixed-limit policy, economic store ve historical run store kaynakları doğrudan incelendi.
- Mevcut tam regresyon: `uv run --frozen python tools/run_checks.py` → `325/325 PASS`.
- Derleme: `uv run --frozen python -m compileall -q src tests` → `PASS`.
- Workspace: `uv run --frozen python tools/check_workspace.py` → `PASS`; `138` aktif Python dosyası.
- Kod değişikliği: yok. Bu alt faz yalnız evidence inventory ve karar kapısıdır.

## Sonuç ve sonraki geçiş

`P1.16.i.a` tamamlandı. Yerel kanıt, stress metadata kimliğinin mevcut olduğunu fakat ekonomik stress modelinin mevcut olmadığını açıkça gösteriyor. Bu nedenle `P1.16.i.b` için exact stress economic contract araştırması gereklidir; rapor gelmeden yeni ekonomik runner, numeric purge/embargo, optimizer, reserve adapter, public API veya UI açılmayacaktır.
