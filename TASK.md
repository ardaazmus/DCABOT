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
- Bağımsız inceleme (review=NOT_RUN) kim/ne zaman?

## Değişmez sınırlar (sürüyor)
- Credential, secret, gerçek emir, mutation ve mainnet: açık onay olmadan asla.
