# P1.13.g.f — DCABOT yerel Futures Grid lifecycle politika sözleşmesi

## Sonuç

- Alt faz durumu: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Yerel offline politika: `CONTRACT_DECLARED`
- Vendor-eşdeğer ileri lifecycle implementation: `DEFERRED / NO-GO`
- Ana faz: `P1.13.g IN_PROGRESS / IMPLEMENTATION_PENDING`
- Kod: `src/dcabot/application/futures_grid_local_policy.py`
- Odak test: `tests/test_futures_grid_local_policy.py` — `2/2 PASS`
- Önceki g.a–g.c gate kümesi: `10/10 PASS`; g.d/g.e araştırma kontrolleri ayrı
  ayrı `3/3 PASS`
- Production readiness: `NO`
- Bağımsız review: `NOT_RUN`

## Açılan güvenli sınır

Kullanıcı tarafından DCABOT’un kendi ürünü için seçilen konservatif yerel
kurallar salt-okunur typed bir değer olarak kayda alındı:

- cancel ile yarışan kabul edilmiş fill yerel ekonomik gözlemde önceliklidir;
- replacement kabulü cancel terminal onayı gelmeden açılmaz;
- reserve release yalnız terminal exchange event gözlemine bağlanır;
- aynı trade kimliğinin aynı içeriği tekrarlandığında yok sayılır;
- bilinmeyen veya çelişkili event quarantine/fail-closed kalır;
- replay deterministic olmadan kabul edilmez.

Bu kararlar 3Commas, Pionex veya Binance’in gizli/eksik belgelenmiş
uygulaması olarak sunulmaz. Fonksiyon order, fill, reserve, state transition,
economic posting, persistence, API/UI veya venue authority üretmez; tüm
authority alanları `NONE` ve kapsam `DCABOT_OFFLINE_SIMULATION_ONLY` olarak
sabitlenmiştir.

## Bilinçli kapsam dışı

Exact vendor lifecycle oracle’ı bulunmadığı için bu politika gerçek borsa
davranışını doğrulamaz. Dynamic range, replacement/cancel execution, reserve
mutation, accepted fill, replay store, signed request, Testnet/live order ve
mainnet açılmadı. Sonraki güvenli iş, yalnız bu açık yerel politika üzerine
kurulacak offline lifecycle transition simülasyonudur; vendor parity iddiası
oluşturulamaz.

## Kontroller

- TDD RED: yeni test, modül henüz yokken beklenen import hatası verdi.
- TDD GREEN: `2/2 PASS`.
- İlişkili Futures Grid gate testleri: `8/8 PASS`.
- `python -m compileall -q src`: `PASS`.
- `git diff --check`: `PASS`.
- `tools/check_workspace.py`: çalıştırıldı; bundled Python `3.12` ile checker’ın
  istediği Python `3.13` bulunmadığından `FAIL` (ortam önkoşulu, kaynak hatası
  değil). Önceki checkout workspace kanıtı korunmuştur.
- Gerçek API key/secret, signed request, order mutation, mainnet ve
  persistence eklenmedi.
