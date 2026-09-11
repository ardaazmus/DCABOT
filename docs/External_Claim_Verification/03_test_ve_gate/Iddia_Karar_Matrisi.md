# İddia karar matrisi

CONFIRMED işaretleri yalnız belirtilen semantik veya baseline doğrulamasıdır; local kodun geçtiği anlamına gelmez.

| ID | İddia | Sınıf | Kaynak/kanıt | Local kanıt | Production etkisi |
| --- | --- | --- | --- | --- | --- |
| C01 | Generic fixed-limit policy DCA state-machine’e doğrudan bağlanmamalı | CONDITIONAL | S01, S03, S06; türetilmiş sınır analizi | Adapter guard, tek commit ve atomik lifecycle; doğrudan çağrı tek başına hata değildir | Kanıt yokken ertele |
| C02 | BASE-only ilk aday olarak daha küçük kapsamlıdır | CONDITIONAL | Baseline rol bağımlılıkları; S09 yalnız analoji | BASE initial predicate; SAFETY/EXIT unreachable; bağımlılık sayısı ve çağrı zinciri | İlk test kapsamını daralt |
| C03 | Observation ve economic fill ayrılmalıdır | CONFIRMED | Baseline + S01 farklı mesaj amacı; S04 veri sınırı | Candidate ekonomik alanları değiştiremez; reducer kabulü izlenir | Semantik ayrım zorunlu; ayrı sınıf seçimi koşullu |
| C04 | Pending BASE reserve lifecycle’ı binding blocker’ıdır | LOCAL-CODE-REQUIRED | S03 dış hold örneği; baseline risk sınırı | Commitment owner, acquisition/reduction/release ve blocker geçişleri | Kapanana kadar ertele |
| C05 | BASE anchor adapter’da değil core’da sahiplenilmelidir | CONDITIONAL | Baseline tek authority; analitik çıkarım | Anchor yetkisi ve partial/full/final event bağı; saf helper delegation sınırı | Tek otorite kanıtı iste |
| C06 | Placement barı fill için eligible olmamalıdır | CONDITIONAL | Baseline; S05, S06, S07 timing örnekleri | Close sonrası intent ve eligible boundary; bar identity kontrolü | Bu baseline’da zorunlu |
| C07 | Equality touch tek başına strict synthetic fill üretmemelidir | CONFIRMED | Strict baseline tanımı; S06 sınırlı örnek | BUY <, SELL >; tick/string exact kıyas; equality no-op | Seçilen profile göre uygula |
| C08 | Ambiguous same-bar ordering’de yeni ekonomik commit yapılmamalıdır | CONDITIONAL | Baseline; S04, S05; bağımsız yol karşı örneği | İlk sıra bağımlı olaydan önce guard; prefix korunumu | Bu profile göre durdur |
| C09 | EOF pending order sentetik olarak kapatılmamalıdır | CONDITIONAL | Baseline; S03 ve S15 TIF/olay ayrımı | EOF yalnız gözlem sonu; fill/cancel/expiry/exit üretmez | Baseline’da OPEN_AT_END koru |
| C10 | Duplicate/late fill idempotency kanıtı gerekir | CONFIRMED | S01 kimlik kavramları; S14 tekrar yan etkileri | Aynı ID aynı payload, çelişkili payload ve bilinmeyen geç event ayrımı | Local test geçmeden ertele |
| C11 | SAFETY ve EXIT BASE ile aynı ilk fazda açılmamalıdır | CONDITIONAL | Baseline aşamalandırma; rol risk analizi | Role guards, bağımsız sonraki faz acceptance kapsamları | İlk adayda deferred tut |
