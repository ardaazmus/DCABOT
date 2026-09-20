# Aktif iş — Faz 1: kod borcu ve bulgu kapatma

Hedef: `DCABOT_HATA_RAPORU.md` yalnız gerçekten açık maddeleri içersin ve bu maddeler kapansın.
Süre kutusu: 1–2 oturum. Bu alt sistemde ardışık dilim: 0/3.

## Adımlar (sırayla; her adım ayrı küçük commit)
1. Raporu güncelle: #2 (`_quality_response`) koddaki `Cache-Control: no-store` ile düzelmiş, #6 (`FAILED` önceliği) hydration'da "en kötü durum kazanır" = fail-closed tasarım → ikisini kapalı işaretle. Test sayısını 865 yap. Sadece belge değişikliği.
2. `api.py`: config'i her istekte diskten okumayı bırak (modül düzeyi cache, mtime ile yenile) — rapor #4. Önce test.
3. `api.py`: CORS izinli origin listesini ortam değişkeniyle yapılandırılabilir yap; varsayılan mevcut 5173 kalsın, wildcard yok — rapor #8.
4. `frontend/src/App.tsx`: 51 `useState`'i `useReducer` veya durum gruplarına böl (`datasetState`, `simulationState`, `savedRunsState`). Davranış değişmez; `tsc -b` ve vitest 12/12 yeşil kalmalı — rapor #10.
5. Rapor #9 (global state) için tek satırlık sınır notu ekle: "uvicorn tek worker". Kod değişikliği yok.
6. `engine.py:292`: STATE.md "bekleyen karar 1"e bağlı. Karar gelmediyse bu adımı atla; Faz 1 kapanışını engellemez.

## Kabul
- Tam checker PASS, frontend tsc + vitest PASS.
- Hata raporu boş veya yalnız "kabul edilen sınır" satırları içeriyor.
- Kapanışta: STATE.md güncellenir, TASK.md Faz 2.1 (demo akışı denetimi) için yeniden yazılır.
