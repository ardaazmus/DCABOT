# İnceleme envanteri

Kaynak commit: `318e1c409ff67083168b31fdd5a27fb28ec7d5f7`. Kaynaklar salt okunur checkout üzerinden incelendi; takipli dosyalarda değişiklik yok. DB dosyalarının içeriği açılmadı.

## Ölçüm

- Depodaki Markdown: **94 dosya**, **17,918 satır**, **1,281,066 byte**.
- Yalnız docs/: **77 Markdown**, **11,637 satır**.
- Byte olarak aynı Markdown grubu: **4**; toplam fazla kopya: **4**.
- Bu byte/satır sayısı context/token faturası ölçümü değildir. HTML prototipler bu Markdown sayısına dahil değildir.

## Anlamsal kapsam

TAM_METIN: yönetim/aktivasyon/context dosyalarının tam metni incelendi. HEDEFLI_BOLUM: finans, execution, DCA, mimari ve test iddialarının ilgili bölümleri okundu. ENVANTER_YALNIZ: yol/boyut/hash ve bazı başlıklar tarandı; tam doğruluk değerlendirmesi yapılmadı. Arşiv, grid/hybrid/ikinci venue ve eski master'ın tüm satırları denetlenmiş sayılmaz. Kesin liste [source_manifest.json](source_manifest.json) içinde.

Kodda hedefli tam dosya incelemesi: domain/dca_math.py, liquidation.py, numeric.py, dca.py, pnl.py, fees.py, reconciliation.py, approval.py; replay/dca_strategy.py, runner.py, realized.py, multi_pair_orchestrator.py; server/daemon.py, recovery.py; security/key_validator.py; tools/run_testnet_harness.py. Persistence/store.py, venue/binance_gateway.py, meta/test_ast_gates.py ilgili bölümleri ayrıca incelendi. Dockerfile/docker-compose.yml ve pyproject.toml okundu. Tüm kaynak/test satırları denetlenmedi.

## Aynı içerik grupları

- `docs/yeni/00_OKU_BENI.md`
- `docs/yeni/PROJE_KANIT_VE_KOD_KALITESI_MD_PAKETI/00_OKU_BENI.md`

- `docs/yeni/01_MASTER_PLAN_DUZELTME_KAYDI.md`
- `docs/yeni/V3_MASTER_PLAN_EK_ARASTIRMALAR/V3_MASTER_PLAN_EKLERI/docs/research/v3/01_MASTER_PLAN_DUZELTME_KAYDI.md`

- `docs/yeni/AGENTS.md`
- `docs/yeni/PROJE_KANIT_VE_KOD_KALITESI_MD_PAKETI/AGENTS.md`

- `docs/yeni/V3_EK_ARASTIRMA_REHBERI.md`
- `docs/yeni/V3_MASTER_PLAN_EK_ARASTIRMALAR/V3_MASTER_PLAN_EKLERI/V3_EK_ARASTIRMA_REHBERI.md`

## Kaynak bütünlüğü

source_manifest.json her Markdown için SHA-256 içerir. Bu manifest içerik provenansını kaydeder; içerikteki iddiaların doğru olduğunu kanıtlamaz. Özgün dosyalar ZIP içinde tekrar çoğaltılmadı; sabit Git commit adresleri kullanıldı.
