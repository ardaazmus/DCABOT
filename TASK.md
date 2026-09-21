# Aktif iş — yok (P4 hariç yol haritası kapalı)

F11 kapandı (checker 1276/1276, vitest 131/131, 29 yeni test,
E2E smoke PASS, gate F11 PASS, kanıt evidence/F11/SONUC.md).

## Durum
12/12 kapı PASS: F1 F4 F5 F6 F7 F8 F9 F10 F11 F11.1 F20 F27.
Çalıştırma: `tools/run_api.py` (tek worker) + `frontend` build.

## Arda'ya açık sorular
- Canary: tutar üst sınırı, günlük kayıp, pencere, min işlem,
  onay artefaktı formatı ne olsun? (`config/canary.json` DRAFT)
- Dış LLM asistanı açılsın mı? (credential + ürün kararı)
- NVDA/JAWS/HCM insan kapısı ne zaman?
- Faz 12 ayrıntılı planı yazıldı (docs/ARASTIRMA_UI_TERMINOLOJI_I18N_FAZ12.md);
  Arda onayı bekleniyor — implementasyona geçilmedi.
- Faz 13/14 onayı bekleniyor (kapsam+kaynak: docs/ARASTIRMA_ILERI_BACKTEST_SINYAL_KALITE.md).
  İstatistik katmanı float/Fraction kararı KAPALI (float64, izole `analytics/`
  modülünde, §4).
- 70 modül (küme A-F, docs/ARASTIRMA_UI_TERMINOLOJI_I18N_FAZ12.md §1) hiçbir
  API/CLI ucuna bağlı değil — çoğu bilinçli/belgeli (Faz 5/9 DEFERRED'leriyle
  örtüşüyor), ama canary_policy.py/live_gate.py'nin "kilitli kapı" ifadesi
  dokümantasyon-gerçeklik uyumsuzluğu taşıyor, netleştirilmeli.

## Değişmez sınırlar (sürüyor)
- Credential, secret, gerçek emir, mutation ve mainnet: açık onay olmadan asla.
