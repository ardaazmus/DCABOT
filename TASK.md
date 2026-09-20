# Aktif iş — Faz 3.3 frontend paneli (Codex brief, UI-only, dosya sınırlı)

Backend hazır ve testli (bkz. STATE.md, docs/KARARLAR.md). Bu görev yalnız frontend'e yeni bir salt-okunur panel ekliyor; backend/API sözleşmesi değişmiyor.

## İzinli dosyalar (yalnız bunlar)
- `frontend/src/BinanceAccountPanel.tsx` (YENİ)
- `frontend/src/BinanceAccountPanel.test.tsx` (YENİ)
- `frontend/src/App.tsx` (yalnız: yeni state/fetch fonksiyonu ekleme + panel render'ı; mevcut hiçbir fonksiyonu/state'i silme veya davranışını değiştirme)
- `frontend/src/styles.css` (yalnız ekleme; mümkünse mevcut `.binance-*` sınıflarını yeniden kullan, yeni sınıf ekleme minimum olsun)

Başka hiçbir dosyaya dokunma. STATE.md/TASK.md/docs/*.md'ye dokunma.

## Referans desen (birebir taklit et)
`frontend/src/BinancePublicSnapshotPanel.tsx` — aynı görsel/yapısal desen: `panel-heading` + `eyebrow` + durum etiketi, type guard fonksiyonu (`isBinance...Snapshot`), `dl.binance-snapshot-facts`, `JsonDisclosure` benzeri katlanır bölüm.
`App.tsx`'te `binancePublicSnapshot*` state üçlüsü (satır ~265-267), `binancePublicSnapshotController` ref (satır ~282), `loadBinancePublicSnapshot()` fonksiyonu (satır ~343-367, `fetch` + `AbortController` + hata işleme deseni) ve mount'ta çağrılması (satır ~325) — birebir aynı deseni yeni panel için tekrar et.

## API sözleşmesi (değişmez, yalnız tüket)

`GET /api/testnet/account` → 200:
```ts
{
  environment: "BINANCE_SPOT_TESTNET";
  account_type: string;
  can_trade: boolean;
  can_withdraw: boolean;
  can_deposit: boolean;
  permissions: string[];
  update_time_ms: number;
  balances_count: number;
  balances: Array<{ asset: string; free: string; locked: string }>;
  response_sha256: string;
  observed_at_us: number;
  read_only: true;
  credential_required: true;
}
```

`GET /api/testnet/open-orders` → 200:
```ts
{
  environment: "BINANCE_SPOT_TESTNET";
  orders: Array<{
    symbol: string; order_id: number; client_order_id: string;
    side: string; type: string; status: string;
    price: string; orig_qty: string; executed_qty: string;
    time_ms: number; update_time_ms: number;
  }>;
  count: number;
  read_only: true;
  credential_required: true;
}
```

**Önemli:** İkisi de credential ayarlanmadıysa `409` döner, gövde `{"code": "TESTNET_CREDENTIAL_NOT_CONFIGURED", "detail": "...", ...}` (Problem Details). Bu bir HATA değil, **beklenen "henüz kurulmadı" durumu** — kırmızı/alarm göstermeyin, sakin bir bilgi kartı gösterin ("Testnet hesabı henüz yapılandırılmadı" gibi). Diğer 4xx/5xx'ler gerçek hata (mevcut panelin `error` durumu gibi işlenir).

## Görev
1. `BinanceAccountPanel.tsx`: tek bir panel, iki bölüm (bakiye tablosu + açık emir tablosu), üstte "TESTNET" rozeti (`BINANCE_SPOT_TESTNET` göründüğü her yerde). Durum: `idle | loading | ready | not_configured | error`. `credential_required`/`read_only` alanlarını da görünür bir yerde belirt (mevcut public panelin "Önemli sınır" notu gibi — "Bu ekran gerçek emir vermez, testnet sanal bakiyesidir" tarzı bir uyarı ekle).
2. Bakiye tablosu boşsa ("balances: []" ama "balances_count: 0" değilse — yani tümü sıfır) "Sıfır olmayan bakiye yok" gibi boş-durum mesajı.
3. Açık emir tablosu boşsa "Açık emir yok" mesajı.
4. `App.tsx`'e `loadBinanceAccountSnapshot()`/`loadBinanceOpenOrders()` (veya ikisini tek fonksiyonda birleştirebilirsin) ekle, mount'ta `loadBinancePublicSnapshot()` ile aynı yerde çağır, panel'i `<BinancePublicSnapshotPanel .../>`'den hemen sonra (App.tsx satır ~915) render et.
5. Test: en az — ready/not_configured/error durumlarının doğru render olduğu, boş bakiye/emir listelerinin doğru mesajı gösterdiği.

## Durma koşulları (brief dışına çıkma)
- Backend'e, API sözleşmesine, credential akışına dokunma.
- Yeni bir fetch endpoint'i icat etme; yalnız yukarıdaki ikisini kullan.
- Emin olmadığın bir görsel karar için mevcut public panelin desenini birebir kopyala, yeni bir tasarım icat etme.
- İşin bitince ne yaptığını, hangi kararları aldığını ve varsa sınırlamaları kısa bir raporla bildir (Claude review edip commit edecek).

## Kabul
- `npx tsc -b` temiz, `npx vitest run` tüm testler PASS (yeni + eski).
- Claude diff'i inceleyip tam checker + tsc/vitest'i kendisi tekrar çalıştırıp commit edecek.
