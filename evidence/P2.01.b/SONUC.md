# P2.01.b — Binance Spot Testnet public snapshot salt-okunur UI

## Sonuç

```text
P2.01.b = IMPLEMENTED_WITH_LIMITATION
IMPLEMENTATION_GATE = READY_WITH_LIMITATION
RENDERED_BROWSER_QA = COMPLETE_WITH_LIMITATION
ACCOUNT_CAPABILITY = NOT_IMPLEMENTED
ORDER_PATH = NOT_IMPLEMENTED
TRADING_ACTIVATION = NO-GO
PRODUCTION_READINESS = NO
```

P2.01.a’nın public `exchangeInfo` snapshot’ı mevcut React stüdyo ekranına
salt-okunur bir kart olarak bağlandı. Kart public venue metadata’sını gösterir;
hesap/API-key yetkisi, bakiye, emir kabulü, fill veya ekonomik sonuç üretmez.

## Uygulanan davranış

- Uygulama açılışında yalnız `GET /api/venue-snapshots/binance-spot-testnet?symbol=BTCUSDT`
  çağrısı yapılır.
- `CONNECTED_READ_ONLY`, `FAILED` ve yükleniyor durumları metinle gösterilir.
- Sembol status’ü ham değerle ve tanımlı nötr açıklamayla gösterilir; bilinmeyen
  status fail-closed olarak `UNKNOWN` görünür.
- `base_asset`, `quote_asset`, `permission_sets`, gözlem zamanı ve venue’un
  bildirdiği `order_types` gösterilir.
- Rate limits, symbol/exchange filters ve snapshot hash native disclosure içinde
  teknik ayrıntı olarak açılır.
- `permissions` yalnız ham public alan olarak gösterilir; account veya key
  yetkisine çevrilmez.
- Kalıcı uyarı: public metadata hesap/API-key trade yetkisi veya fill kanıtı
  değildir; Testnet sanal ve resetlenebilir bir ortamdır.
- UI tarafında bakiye, reserve, PnL, fee, exposure, order oluşturma veya fill
  hesabı yoktur.

## Değişen dosyalar

- `frontend/src/BinancePublicSnapshotPanel.tsx`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- P2.01.a public contract: `src/dcabot/data_adapters/binance_testnet_public.py`,
  `src/dcabot/server/api.py`
- P2.01.a odak testleri: `tests/test_binance_testnet_public.py`,
  `tests/api/test_binance_testnet_public.py`

## Kanıt

| Kontrol | Sonuç |
|---|---|
| Frontend TypeScript + Vite build | `PASS` |
| Public adapter/API odak testleri | `7/7 PASS` |
| Tüm Python regresyonu | `366/366 PASS` |
| Python 3.13 compileall | `PASS` |
| Workspace kontrolü | `PASS`, 150 aktif Python dosyası |
| Gerçek public Testnet GET | `PASS`, `BTCUSDT=TRADING`, 11 filter, 4 rate limit |
| Yerleşik tarayıcı DOM/screenshot/interaction QA | `NOT_RUN`: browser çalışma varlık yolu bulunamadı |
| Doğrudan Chrome CDP responsive/visual QA | `PASS`: 320/768/1280px’te yatay taşma yok; snapshot ve public/account sınırı DOM’da mevcut; screenshot kanıtı `.cluster/p2-audit-20260911/p2-01b-{320,768,1280}.png` |
| Doğrudan Chrome CDP keyboard/focus QA | `PASS`: 23 klavye durağında görünür focus ring; Space ile native disclosure aç/kapa doğrulandı |
| Güncel kaynakla yeniden başlatılmış local API route smoke | `PASS`: HTTP 200; `BINANCE_SPOT_TESTNET`, `BTCUSDT`, `TRADING`, `read_only=true`, `credential_required=false`; order types döndü |
| NVDA/JAWS/Windows HCM | `NOT_RUN` |
| Signed account/order/mutation | `NO-GO`, çalıştırılmadı |

## Sınırlar ve sonraki adım

Bu dilim P2.01.b public read-only UI’sını derlenebilir, sözleşme kontrollü,
güncel local API ile erişilebilir ve doğrudan Chrome CDP ile 320/768/1280px
responsive/visual/keyboard smoke doğrulanmış hale getirir. Yerleşik browser
eklenti yolu çalışmadı; bu nedenle plugin tabanlı otomasyon ve gerçek NVDA/JAWS/
Windows HCM hâlâ `NOT_RUN` durumundadır. Bu kayıt production accessibility veya
tam WCAG uygunluk iddiası değildir. P2.02 signed secret/outbox, P2.03 order
lifecycle ve P2.04 reconciliation bu kartın kapsamı değildir.
