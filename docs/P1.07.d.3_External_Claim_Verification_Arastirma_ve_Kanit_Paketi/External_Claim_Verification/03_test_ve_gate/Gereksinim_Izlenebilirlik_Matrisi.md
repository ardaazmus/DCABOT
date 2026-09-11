# Gereksinim izlenebilirlik matrisi

Bu belge gereksinimin raporda karşılandığı yeri gösterir; local testlerin geçtiğini göstermez. Bölüm numaraları ana rapora aittir.

| İstek | Konu | Kapsayan bölüm/dosya | Kanıt veya test ilişkisi |
| --- | --- | --- | --- |
| A1 | Generic policy doğrudan bağlama riski | §1, §3, §7.4 | T08,T30 |
| A2 | Observation/candidate/economic fill ayrımı | §2, §7.3–7.4 | T03,T30 |
| A3 | Bağlanabilirlik production yeterliliği | §3, §15, §17 | Gate C |
| A4 | Kanıtsız production erteleme makullüğü | §1, §16–17 | Gate A–D |
| A5 | Kesin/koşullu/implementation-dependent sınırı | §2–4 | C01–C11 |
| B1 | BASE daha az bağımlılık | §7.1, §12 | Role analizi |
| B2 | BASE-only vertical slice denetlenebilirliği | §5.3, §7 | Gate C |
| B3 | Partial/complete/no-fill ayrımı | §9.4, §13.2 | T04–06,T15 |
| B4 | BASE tamamlanmadan SAFETY planı/risk | §12.1 | T05,T07 |
| B5 | Upstream/downstream state kanıtı | §7.2–7.4 | Gate A,C,D |
| C | Event ve lifecycle bütün adımları | §7.3, §9.4 | Owner/girdi/mutasyon/çıktı/kanıt tablosu |
| D1 | Pending BASE commitment | §8.1 | T07,T29 |
| D2 | Reserve acquisition timing | §8.2 | A09,D |
| D3 | Partial reserve/leaves ilişkisi | §8.3 | T04,T29 |
| D4 | Equality reserve tüketimi | §8.3 | T02,T29 |
| D5 | Ambiguity ve OPEN_AT_END reserve | §8.3, §10.5–10.6 | T10,T11,T29 |
| D6 | Yeni formül yerine domain kanıtı | §8.4 | Gate D |
| D7 | Exchange hold yerel reserve değildir | §4, §8.1 | S03 sınırı |
| E1 | BASE anchor event | §9.1 | A07,T06 |
| E2 | Partial anchor kararı | §9.1 | T04–06 |
| E3 | Adapter anchor çift authority | §7.4, §9.1 | T30 |
| E4 | Anchor/average/cost basis eşitliği | §9.2 | Gate D |
| E5 | Coverage ve quantity complete | §9.3 | T19 |
| E6 | ORDER_FINAL position/order ayrımı | §9.4 | A11,T11 |
| E7 | Core tek owner tercih gerekçesi | §7.3–7.4, §9.1 | T24,T30 |
| F1 | Placement look-ahead | §10.1 | T01 |
| F2 | ACTIVE_NEXT_BAR koşulu | §10.1 | Gate B |
| F3 | Equality ve strict farkı | §10.2 | T02,T03 |
| F4 | OHLC intrabar sırayı kanıtlamaz | §10.4 | Oracle OHLC karşı örneği |
| F5 | Aynı-bar favorable sıralama | §10.4–10.5 | T10 |
| F6 | Ambiguity prefix koruma | §10.5 | T10 ve property matrisi |
| F7 | EOF ayrı model kararı | §10.6 | T11 |
| G1 | Deterministik replay duplicate nedenleri | §11.1 | T08,T12 |
| G2 | Duplicate ekonomik zarar | §11.1 | T08,T24 |
| G3 | Order/bar/slice dedupe rolü | §11.2 | T16,T17 |
| G4 | Late fill fail-closed/unresolved | §11.3 | T09,T20 |
| G5 | Dış execution ID local contract değildir | §4, §11.2 | S01 sınırı |
| H-SAFETY | Sekiz safety bağımlılığı | §12.1 | Sonraki faz kanıt tablosu |
| H-EXIT | Sekiz exit bağımlılığı | §12.2 | Sonraki faz kanıt tablosu |
| Prompt4 | Kaynak kurum/başlık/URL/tarih/iddia/sınır | §18 ve 02_kanitlar | 15 kart + MD/JSON envanter |
| Prompt5 | 11 iddialık zorunlu karar matrisi | §2.2 ve 03_test_ve_gate | C01–C11 |
| Prompt6 | Gate A inventory, B timing, C integration, D exact | §5 ve 03_test_ve_gate | A01–A11/B/C/D |
| Prompt7 | 14 asgari test ve independent ikinci kontrol | §13 ve tam test matrisi | T01–T14 +16 ek test |
| Prompt8 | 13 beklenen içerik öğesi | §1–18 içinde, son §14 sırası uygulanarak | Summary, evidence, map, blockers, gates, tests, checklist, decision, sources |
| Prompt9 | İddia ayrımı ve RED/GREEN/bağımsız kontrol | §2–5, §13–14 | Local test yapılmış gibi sunulmadı |
| Prompt10 | Dar anonim code-request protocol | §6 ve 05_kod_talebi | Altı sınırlı sembol/test grubu; repo istenmez |
| Prompt11 | Yedi adımlı kesin owner veri akışı | §7.3 | Girdi/mutasyon/çıktı/kanıt |
| Prompt12 | 12 zorunlu BASE-only pre/post senaryo | §13.2 | Ön-state/post-state/reject/new-risk |
| Prompt13 | 12 kesin durdurma kuralı | §16 | Gözlenen ihlal / kanıt eksikliği ayrımı |
| Prompt14 | 18 bölüm sırası ve dört satırlık son alanlar | Ana rapor | 18 bölüm;18 durum,kanıt,etki,kapanış seti |
| Prompt15 | Anonimlik ve kapsam | Tüm paket | Private proje/path/account/credential yok; synthetic fixtures |
