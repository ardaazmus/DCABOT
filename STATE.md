# Durum — 2026-09-21 (P4 hariç TAMAM)

Aktif iş: **yok — yol haritası P4 hariç kapalı.** 12/12 kapı PASS.
Dal: codex/latest-state-2026-09-20.
Doğrulanan: checker 1277/1277 PASS, tsc temiz, vitest 136/136,
vite build + E2E serve smoke PASS.
Eksenler: implementation=COMPLETE · verification=PASS ·
evidence_scope=LOCAL_INTEGRATION(+canlı public venue) · review=APPROVED ·
deployment=NOT_DEPLOYED

## Kapanış (bu oturum)
F11.2–7: dağıtım, form ailesi, sihirbaz, tablo, bildirim, render.
E2E: API + production build serve OK.

## Bilinen sınırlar
- DCA/paper/bot session RAM'de; şablon/two-leg/deal dosyada kalıcı.
- Testnet'te 0.0004 BTC açık (zararsız). Mainnet kesin NO-GO.
- NVDA/JAWS/HCM NOT_RUN (insan kapısı). Dış LLM DEFERRED.
- review=APPROVED (2026-09-21, bağımsız oturum/Claude, salt okunur,
  ardından derin çok-ajanlı kod incelemesi): 3 gerçek hata bulunup
  düzeltildi — TemplatePanel bind `config_hash` yanlış alanda arandığı
  için her zaman "doğrulanamadı" gösteriyordu; SHORT futures trailing
  `high_water` beklerken backend `low_water` döndürdüğü için SHORT
  ucu kullanılamıyordu; testnet open-orders'ta geçersiz `symbol`
  girdisi 503 (sunucu kesintisi) olarak yanlış raporlanıyordu (artık
  400). Üçü de regresyon testiyle kilitlendi, tam checker+tsc+vitest
  yeniden PASS. Ertelenen (küçük/kapsam dışı, düzeltilmedi): 404/409
  yerine her yerde 422 dönmesi, birkaç UI pencereleme/reuse notu —
  `docs/KARARLAR.md`'de.

## Arda kararları (açık)
Canary sayısal değerleri + onay formatı; dış LLM; P4 kapsamı.
