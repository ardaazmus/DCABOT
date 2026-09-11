# P1.01 — local UI/API preview kanıtı

Durum: `IMPLEMENTED / LOCAL_PASS`; Browser E2E: `PASS`; review: `NOT_RUN`

## Uygulanan davranış

- `POST /api/preview`, varsayılan `config/paper.json` ile yalnız formdan gelen `anchor`, `safety_qty`, `safety_count`, `deviation` alanlarını birleştirir ve mevcut `application.service.preview()` yolunu çağırır.
- Finansal değerler API sınırında noktasız Decimal JSON string olarak kalır; yanlış tip alan bazlı `422` döndürür.
- React ekranı form → API → mevcut çekirdek → ladder/economic summary akışını gösterir.
- Her istek monotonic `revision` taşır; önceki yanıt yeni revision’ın state’ini ezemez.
- Local-only/offline durum, credential ve testnet yollarının kapalı olduğu metinsel olarak görünür.

## Kanıt

| Kontrol | Komut / kapsam | Sonuç |
|---|---|---|
| Python bağımlılık kilidi | `uv lock --check --python Python313` | PASS |
| Python testleri | `uv run --frozen ... python tools/run_checks.py` | PASS — 41 test |
| Frontend build | `npm run build` | PASS — Vite 7.3.6 |
| Runtime dependency audit | `npm audit --audit-level=high` | PASS — 0 vulnerability |
| Health HTTP | `GET http://127.0.0.1:8000/api/health` | PASS — offline, trading disabled |
| Preview HTTP | `anchor=100`, `safety_qty=1`, `safety_count=2`, `deviation=0.1` | PASS — levels 90/80, gross 270, IM 270 |
| Validation HTTP | `anchor=100` numeric | PASS — 422, `fields.anchor` |
| Vite proxy HTTP | `POST http://127.0.0.1:5173/api/preview` | PASS — levels 90/80, gross 270, revision preserved |

## Browser kanıtı

- `http://127.0.0.1:5174/` page identity/title doğru; DOM anlamlı ve framework overlay yok.
- DEMO: `90/80`, gross `270`, IM `270`.
- Anchor değişimi: `120` → `108/96`, gross `324`.
- `abc` hatası: Türkçe alan uyarısı; eski `324` ladder/özet temizlendi.
- 360×800: `scrollWidth=345`, yatay taşma yok; ekran ve Local-only metin mevcut.
- 1280×800: `scrollWidth=1280`, Notional sütunu görünür; ekran ve Local-only metin mevcut.
- Browser console error/warn: yok.

## Açık kapılar

- Bağımsız ikinci Codex incelemesi `NOT_RUN`.
- CSV/ZIP import, public historical downloader ve P2 testnet bu görevin kapsamı değildir.
