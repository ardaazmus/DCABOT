# Çalışma düzeni

## Oturum döngüsü
1. `git status --short` ve mevcut commit. Kullanıcı değişikliklerine dokunma.
2. AGENTS.md, STATE.md, TASK.md oku. TASK.md'deki işi bitirmeden yeni iş seçme. TASK yoksa YOL_HARITASI "Şimdi" bölümünden tek iş seç.
3. `rg` ile ilgili sembolleri ve çağıranları bul. Dosya yolunu tahmin etme.
4. Yanlış davranışı gösteren bağımsız bir test/örnek yaz (finansal hesapta elle veya rasyonel hesaplanmış sonuç). Sonra minimal düzeltme.
5. Odak testleri, sonra tam checker. Çıkış kodunu ve eksikleri not et.
6. Diff'i incele: görev dışı değişiklik, geriye dönük uyum, kimlik/dedup kaybı, recovery etkisi.
7. STATE.md'yi yeniden yaz (anlık fotoğraf), TASK.md'yi sıradaki iş için yeniden yaz.

Bağlam dolarken yeni işe başlama: diff'i tutarlı bırak, test edilmediyse açıkça yaz.

## Durum eksenleri
- implementation = NOT_STARTED | IN_PROGRESS | IMPLEMENTED
- verification = NOT_RUN | PASS | FAIL | INCONCLUSIVE
- evidence_scope = UNIT | LOCAL_INTEGRATION | REAL_TESTNET | CANARY
- review = NOT_RUN | CHANGES_REQUESTED | APPROVED
- deployment = NOT_DEPLOYED | TESTNET | MAINNET

Yerel PASS, REAL_TESTNET yapmaz. Faz ancak kendisine gereken eksenler tamamlanınca kapanır. Bağımsız doğrulama yapılmadıysa "doğrulandı" yazma.

## Araştırma kutusu
Bilinmeyen bir davranış için: (1) yerel kaynak ve testleri tara, (2) karşı-örnek/RED test dene, (3) resmi birincil kaynağa bak, (4) gerekirse üretim kodundan bağımsız küçük bir oracle yaz. Bunlar tek oturumda yapılır. Sonuç yetersizse ≤ 10 satırlık karar notu yaz ve Arda'ya soru sor; aynı belirsizlik için ikinci bir araştırma oturumu açma.

## Çoklu yapay zekâ
- Aynı working tree'ye iki model aynı anda yazmaz (WIP=1).
- Model değişiminde devir: taban commit, diff, TASK.md, kalan tek iş. Sohbet dökümü devredilmez.
- Paralel çalışma ayrı dal/worktree ve çakışmayan dosya sahipliği ister; tek kişi birleştirir.
- Review ayrı oturumda, salt okunur yapılır. Faz kapanışında yapılır.

## Faz sonu kontrolü (5 dakika)
- Faz kaç dilimde bitti; kaçı kullanıcı-görünür sonuç üretti?
- Aynı alt sistemde ardışık dilim sayısı ≤ 3 mü?
- STATE/TASK boyutu limitte mi (checker söyler)?
- Review ilk seferde kabul edildi mi; geri dönen bulgu sayısı?
