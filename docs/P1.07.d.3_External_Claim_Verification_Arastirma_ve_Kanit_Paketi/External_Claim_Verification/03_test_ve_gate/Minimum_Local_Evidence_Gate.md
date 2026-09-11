# Minimum local evidence gate

Tüm satırlar: LOCAL-CODE-REQUIRED — KANIT YOK. Kaynak dosya adı veya yol uydurulmamıştır; yalnız modül rolü/test türü istenir.

| Gate | Claim | İstenen kaynak/test türü | Input fixture | Beklenen transition | Counterexample test | Ekonomik risk |
| --- | --- | --- | --- | --- | --- | --- |
| A01 | INTENT kabulü order active yapar | Order/state types + intent reducer + call-site test | Boş state; valid BASE intent | Tek immutable order, placement/eligibility/blocker; kabul ve aktivasyon ayrıysa açık iki aşama | T07,T27 | Aktif olmayan emirden fill |
| A02 | INTENT ekonomik fill oluşturmaz | Intent reducer unit + integration test | T01 pre-state | Qty/cost/realized/fee değişmez; commitment değişimi ayrı allowed | T01,T30 | Hayalet pozisyon |
| A03 | Yalnız yetkili FILL trade accounting yazar | Reducer FILL/MARK/FINAL branch ve mutation audit | Candidate, MARK, FINAL ayrı events | FILL trade ledgerı; MARK yalnız valuation; rezerv metadata başka lifecycle’da olabilir | T25,T26,T30 | Sessiz maliyet/fill kayması |
| A04 | Partial exact leaves | Fill reducer + quantity type test | Q=.30; q=.10 | filled=.10; leaves=.20; order partial | T04,T18 | Overfill / residual kaybı |
| A05 | Duplicate ikinci posting yok | Dedupe validation + event chain test | Aynı ID aynı payload iki kez | Economic delta ikinci kez0; pending/terminal ayrımı güvenli | T08,T16,T20 | Çift miktar/fee/reserve tüketimi |
| A06 | Yeni late FILL explicit unresolved | Final/fill ordering + integrity guard | Final sonra unknown execution | Prefix economic unchanged; integrity unknown; risk bloke | T09,T20 | Sahte final veya çift fill |
| A07 | BASE anchor timing açık | Anchor owner + strategy decision call-site | Partial/full/final üç sınır | Domain’in belirttiği tek event anchor yazar; adapter authority yok | T06,T30 | Yanlış safety seviye |
| A08 | Coverage complete açık | Coverage aggregate/final validator | Filled=Q fakat final eksik/çelişkili | Miktar ile kanıt tamamlanması ayrı; domain tamlık koşulu | T05,T19 | Erken next risk |
| A09 | Pending/unresolved yeni riski sınırlar | Pending predicate + risk gate + intent accept | Pending BASE veya UNKNOWN | İkinci risk açılmaz; yalnız belgeli çözücü event serbest | T07,T29 | Aynı kapasitenin tekrar kullanımı |
| A10 | Fee/slippage tek pipeline | Economic helpers + reducer call sites | Fee literal ve declared limit | Fee varlık etkisi tek; price ikinci slippage ile değişmez veya profil çatışması reject | T14,T24 | Çift fee / limit ihlali |
| A11 | ORDER_FINAL order/position ayrımı | Final branch + position predicates | Full BASE sonra final; partial sonra EOF | Order kapanabilir position açık kalır; EOF order’ı filled yapmaz | T11,T19 | Sahte düz pozisyon |
| B | Historical timing | Strategy decision loop + policy eligible check | Placement/equality/strict/ambiguity/EOF | Close boundary ve ilk belirsiz event sınırı açık | T01–03,T10–12,T15,T21–22 | Look-ahead / sıra uydurma |
| C | BASE-only vertical slice | Actual intent→adapter→reducer→next-decision integration | No-fill, partial, full+final | Gerçek çağrı zinciri; SAFETY/EXIT unreachable; legacy unchanged | T01–13,T17,T23,T27,T30 | Sadece yardımcı testine güvenme |
| D | Exact accounting | Independent domain ledger + reference oracle + observed state | Qty, price, fee asset, position cost, anchor, commitment, final/open | Her economic alan bağımsız beklenene eşit; bilinmeyen numeric alan sıfıra doldurulmaz | T04,T14,T18,T24–25,T28–29 | Self-verifying test / yanlış reserve |
