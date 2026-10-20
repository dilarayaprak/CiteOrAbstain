# Teknoloji Kararları (Türkçe)

Bu belge CiteOrAbstain projesinde hangi teknolojileri seçtiğimizi, neden seçtiğimizi ve bu kararları hangi deneylere dayandırdığımızı anlatır. İngilizce belgenin ([technology_decisions.md](technology_decisions.md)) Türkçe karşılığıdır. Ondan farkı, her bölümde **kavram açıklamaları** bulunmasıdır: konuya yeni başlayan bir ekip arkadaşı da okuyup anlayabilsin diye yazıldı.

Deneylerin kodları `notebooks/` klasöründedir. Bir sonucu kendin görmek istersen ilgili dosyayı çalıştırabilirsin (bkz. en alttaki "Deney Listesi").

Hazırlayan: Dilara Yaprak — Son güncelleme: Ekim 2026 (2. hafta)

---

## Önce Büyük Resim: Sistem Nasıl Çalışıyor?

Projemiz bir **RAG** sistemi. RAG (Retrieval-Augmented Generation, "bilgi getirerek desteklenmiş metin üretimi") üç adımdan oluşur:

1. **Retrieval (getirme):** Kullanıcının sorusuna en çok benzeyen metin parçalarını belge veritabanından bulmak.
2. **Augmentation (destekleme):** Bulunan parçaları soruyla birlikte dil modeline vermek.
3. **Generation (üretme):** Dil modelinin (LLM) **yalnızca bu parçalara dayanarak** cevap yazması ve kaynağını göstermesi (**citation / atıf**).

Bizim sistemimizin özel yanı **abstention (çekimser kalma)**: Cevap belgelerde yoksa ya da soru ilaç/acil durumla ilgiliyse sistem cevap uydurmaz, *"Bilmiyorum, lütfen sağlık ekibinize danışın"* der. LLM'lerin kaynakta olmayan bilgiyi kendinden uydurmasına **hallucination (halüsinasyon)** denir; çekimser kalma bunu önlemenin yoludur.

Bu belgedeki her teknoloji bu zincirin bir halkasıdır:

```text
Web sayfası ──► Metin çıkarma ──► Parçalama ──► Embedding ──► Vektör veritabanı
                (trafilatura)     (chunking)    (MiniLM)      (ChromaDB)
                                                                   │
Kullanıcı sorusu ──► Güvenlik kontrolü ──► En benzer 5 parça ◄─────┘
                     (ilaç/acil?)              │
                                               ▼
                                     Eşik değerini geçti mi?
                                      ├─ Evet → LLM cevap + kaynak (Ollama)
                                      └─ Hayır → "Bilmiyorum..."
                                               │
                                       Streamlit arayüzü
```

---

## Karar Özeti

| Alan | Seçim | Durum |
|---|---|---|
| Programlama dili | Python 3.12 | Kesin |
| Paket yönetimi | `requirements.txt` (sabit sürümler) + kilit dosyası | Kesin (kilit dosyası öneri) |
| Sürüm kontrolü | GitHub, branch + Pull Request düzeni | Kesin (takım kuralları öneri) |
| Metin çıkarma | `requests` (ham bayt) + `trafilatura` | Geçici (3 kaynakta test edildi) |
| Parçalama | Bölümlere göre, ~120 kelime, 25 kelime örtüşme, ≤ 256 token | Geçici (soru setiyle doğrulanacak) |
| Embedding | sentence-transformers, `all-MiniLM-L6-v2` (aday: `all-mpnet-base-v2`) | Geçici |
| Vektör veritabanı | ChromaDB, cosine benzerliği | Geçici (takım onayı bekleniyor) |
| Getirme | Top-K = 5 | Geçici |
| LLM (yerel) | Ollama + `llama3.2` (3B) | Geçici |
| LLM (hosted) | Henüz seçilmedi | Açık |
| Web arayüzü | Streamlit | Kesin |
| Paketleme | Docker Compose | Kesin (projenin sonunda yazılacak) |
| Soru dili | İngilizce | Geçici (danışman onayı bekleniyor) |

**Durumların anlamı:** *Kesin* = değişmesi beklenmiyor. *Geçici* = bununla ilerliyoruz ama değişebilir. *Açık* = henüz karar verilmedi.

---

## 1. Programlama Dili ve Ortam

**Seçim:** Python 3.12, her bilgisayarda bir sanal ortam (`venv`).

- Proje tanımı Python öneriyor ve kullandığımız her bileşenin (embedding, vektör veritabanı, LLM bağlantısı, Streamlit) Python kütüphanesi var.
- **Neden 3.12?** Daha yeni sürümler (3.13, 3.14) PyTorch, onnxruntime gibi ağır kütüphanelerle uyumsuzluk çıkarabiliyor. 3.12 hepsiyle çalışıyor. Son Docker imajı da aynı sürümü kullanacak.
- **Her zaman `pip` yerine `python -m pip` kullanın.** Bazı antivirüs programları venv içindeki `pip.exe` dosyasını engelliyor.

> **Kavram — Sanal ortam (venv):** Projeye özel, bilgisayarın geri kalanından ayrı bir Python "kutusu". Kurduğumuz kütüphaneler bu kutuya kurulur, başka projeleri bozmaz. Terminalde satırın başında `(venv)` yazıyorsa kutunun içindesin. venv klasörü GitHub'a **yüklenmez** (`.gitignore`); herkes kendi bilgisayarında `requirements.txt`'den yeniden oluşturur.

### Paket (bağımlılık) yönetimi

> **Kavram — Bağımlılık:** Kodumuzun çalışması için gereken dış kütüphaneler. Bunların da kendi bağımlılıkları vardır (dolaylı bağımlılık). Örneğin biz `sentence-transformers` kurarız, o da kendi başına `transformers` kütüphanesini kurar.

- `requirements.txt` yalnızca **doğrudan** kullandığımız kütüphaneleri sabit sürümle tutuyor (örn. `chromadb==1.5.9`, `sentence-transformers==6.1.0`).
- **Gözlenen sorun:** Dolaylı bağımlılıklar sabitlenmediği için kurulumdan kuruluma değişebiliyor. Eski bilgisayarda `transformers 5.18.0`, yeni bilgisayarda `transformers 5.20.1` kuruldu. Bu sefer sorun çıkmadı ama "bende çalışıyor, sende çalışmıyor" sorunlarının tipik sebebi budur.
- **Öneri:** Çalışan bir ortamdaki **her şeyin** tam sürümünü tutan ek bir **kilit dosyası**:
  ```powershell
  python -m pip freeze > requirements-lock.txt
  ```
  `requirements.txt` insanların okuyacağı kısa liste olarak kalır; Docker ve jüri kurulumu kilit dosyasını kullanabilir. Kilit dosyası Windows'a özel paketler içerebilir, bu yüzden Docker'da (Linux) test edilmeli.
- **Bu hafta eklenecekler:** `requests`, `trafilatura==2.3.1`. (`beautifulsoup4` son sistemde gerekmiyor, sadece karşılaştırma deneyinde kullanıldı.)

### Bilinen sorun: Windows 11 Akıllı Uygulama Denetimi (Smart App Control)

- Yeni bir Windows 11 bilgisayarda Akıllı Uygulama Denetimi kendiliğinden *değerlendirme* modundan *açık* moduna geçti ve numpy içindeki imzasız bir dosyayı engelledi:
  `ImportError: DLL load failed while importing _pcg64: Uygulama Denetimi ilkesi bu dosyayı engelledi.`
  Aynı kütüphaneler bir gün önce çalışıyordu.
- **Çözüm:** Windows Güvenliği → Uygulama ve tarayıcı denetimi → Akıllı Uygulama Denetimi → *Kapalı*. Windows Defender antivirüsü çalışmaya devam eder.
- **Dikkat:** Bir kez kapatılınca Windows yeniden kurulmadan tekrar açılamıyor. Windows 11 kullanan ekip arkadaşları aynı sorunla karşılaşabilir.

## 2. Sürüm Kontrolü ve Takım Çalışma Düzeni

**Seçim:** GitHub deposu `dilarayaprak/CiteOrAbstain` (gizli), branch + Pull Request düzeniyle.

> **Kavram — Branch (dal):** `main`'e dokunmayan ayrı bir çalışma hattı. İstediğin kadar değişiklik yaparsın, ana kod bozulmaz.
>
> **Kavram — Pull Request (PR):** "Bu dalı `main`'e ekleyelim mi?" isteği. Ekip arkadaşları GitHub'da değişiklikleri görür, yorum yapar ve onaylar. Onaydan sonra birleştirilir (merge).

```text
main ──●──────────────●──────  (herkesin kullandığı sağlam kod)
        \            /
         ●──●──●───●          (çalışma dalı)
                   ↑
             Pull Request
```

**Neden bu düzen?** `main` her zaman çalışan kodu içerir; her değişikliği en az bir kişi daha görür; inceleme geçmişi GitHub'da görünür (kod kalitesi notun %35'i).

**Önerilen takım kuralları:**
1. `main`'e doğrudan push yok; herkes `isim/konu` adlı bir dalda çalışır (örn. `dilara/week2-research`).
2. Her PR, **en az bir ekip arkadaşı onayladıktan** sonra birleştirilir.
3. Ortak kodlama günlerinde ekip tek bir ortak dalda çalışır (örn. `feature/retrieval-v0`) ve gün sonunda PR açar.
4. İki kişi aynı dosyayı aynı anda ayrı ayrı düzenlemez.
5. Herkes çalışmaya başlamadan önce `git pull` yapar.

Ekip arkadaşları için kurulum adımları: [kurulum_rehberi.md](kurulum_rehberi.md)

## 3. Web Sayfalarından Metin Çıkarma

**Sorun:** İndirdiğimiz web sayfası düz metin değil, HTML'dir. Makalenin yanında menüler, site afişleri, alt bilgiler (footer) de vardır. Bu "gürültü" temizlenmezse veritabanına parça olarak girer ve arama sonucu olarak dönebilir. Örneğin hastaya "NLM Web Policies, Copyright" yazan bir parça gösterilebilir.

> **Kavram — HTML:** Web sayfalarının yazıldığı işaretleme dili. Metnin yanında sayfanın yapısını (başlık, menü, bağlantı) tarif eden etiketler içerir.

**Seçim:** Sayfayı `requests` ile indirip ana içeriği `trafilatura` ile çıkarmak. trafilatura'ya **ham bayt** (`response.content`) veriyoruz.

### Deney 1: BeautifulSoup vs trafilatura (`05_text_extraction_experiment.py`)

- **BeautifulSoup:** HTML'deki **bütün** metni alır, neyin makale neyin menü olduğunu ayırt etmez.
- **trafilatura:** Sayfanın **ana içeriğini** tahmin edip sadece onu alır.

Sayfa: MedlinePlus — Knee joint replacement (https://medlineplus.gov/ency/article/002974.htm)

| | A) BeautifulSoup `get_text()` | B) trafilatura `extract()` |
|---|---|---|
| Uzunluk | 11.736 karakter (1.911 kelime) | 7.342 karakter (1.282 kelime) |
| Başlangıç | "Skip navigation", "An official website of the United States government", kilit simgesi metni | Doğrudan makale: "Knee joint replacement is a surgery to replace a knee joint..." |
| Bitiş | Alt bilgi: "NLM Web Policies", "Copyright", posta adresi | "Updated by: ... 07/01/2025" |

- BeautifulSoup metninin yaklaşık üçte biri (~4.400 karakter, ~%37) gürültüydü.
- trafilatura bunu otomatik temizledi; bölüm başlıklarını ("Description") ve madde işaretlerini korudu.

**Karakter kodlaması (encoding) sorunu:** BeautifulSoup çıktısında "Here's how you know" yerine **"Hereâs how you know"** yazıyordu.

> **Kavram — Karakter kodlaması (encoding):** Bilgisayar harfleri sayı olarak saklar; hangi sayının hangi harf olduğunu gösteren tabloya kodlama denir (en yaygını UTF-8). Yanlış tabloyla okunan metinde ' gibi işaretler "â" gibi anlamsız karakterlere dönüşür.

Site kodlamasını belirtmediği için `requests` yanlış tahmin etti ve UTF-8 karakterleri bozdu. Bozuk kelimeler ("don't", "patient's") embedding ve arama kalitesini düşürür.
**Çözüm:** trafilatura'ya ham bayt (`response.content`) vermek; kodlamayı kendisi doğru tespit ediyor. Düzeltmeden sonra bozuk karakter sayısı **0** oldu (`06_chunking_experiment.py`).

### Deney 2: Diğer kaynaklar (`09_other_sources_test.py`)

| Kaynak | Sonuç |
|---|---|
| **NHS** ana sayfa (`/conditions/knee-replacement/`) | `/tests-and-treatments/knee-replacement/` adresine **yönlendirildi**. Sadece 24 kelime çıktı: bu sayfa bir içindekiler listesi. Asıl içerik **7 alt sayfada**: what-is-a-knee-replacement, why-its-done, alternatives, preparation, how-its-done, recovery, complications. |
| **NHS** Recovery alt sayfası | Çok temiz: 563 kelime, başlıkla başlıyor, bozuk karakter yok. Sonunda gürültü satırları var: "Video: ...", "In this video, ...", "Media review due: 22 May 2029". |
| **NIH NIAMS** `/health-topics/joint-replacement-surgery` | **Sessizce** genel konu listesine (`/health-topics`) yönlendirildi. Diz protezi içeriği yerine 160 kelimelik site afişi ve genel metin çıktı. Durum kodu yine de 200'dü (yani "başarılı" görünüyordu). |

> **Kavram — Yönlendirme (redirect) ve durum kodu:** Bir adres taşındığında site seni otomatik olarak yeni adrese gönderir. Durum kodu 200 "sayfa başarıyla geldi" demektir, ama **gelen sayfanın istediğimiz sayfa olduğunu garanti etmez**. NIAMS örneğinde tam olarak bu oldu.

### Bulgular ve veri hazırlama kuralları

1. **trafilatura** MedlinePlus ve NHS içerik sayfalarında iyi çalışıyor.
2. **Sadece durum koduna değil, son adrese (`response.url`) ve metin uzunluğuna da bakılmalı.** Yönlendirme olursa ya da metin çok kısaysa (örn. < 200 kelime) uyarı verilmeli.
3. **Her NHS alt sayfası ayrı bir kaynaktır.** NHS tek başına 7 kaynak sağlıyor. Güncel `/tests-and-treatments/...` adresleri kullanılmalı.
4. **Siteye özgü gürültü satırları silinmeli:** "Updated by ..." (MedlinePlus), "Video: ...", "In this video, ...", "Media review due: ..." (NHS). Güncellenme tarihi silinmez, kaynak listesine (source registry) yazılır. "References" bölümü de atlanmalı (akademik kaynak listesi, hasta bilgisi değil).
5. **Çıktı dosyaları Python içinden `encoding="utf-8"` ile yazılmalı.** PowerShell'de çıktıyı `>` ile dosyaya yönlendirmek, metnin kendisi doğru olduğu halde bozuk karakterler üretti ("HereÆs").
6. **NIAMS için doğru adres bulunmalı.**

## 4. Parçalama (Chunking): Parça Boyutu ve Örtüşme

> **Kavram — Chunk (parça):** Uzun bir belgenin küçük metin parçalarına bölünmüş hali. Veritabanında aranan ve LLM'e verilen şey sayfanın tamamı değil, bu parçalardır.

**Neden parçalıyoruz?**
1. Bütün sayfa için tek vektör, birçok konuyu karıştırır ve aramayı zayıflatır. "Ameliyatta acı hisseder miyim?" sorusu için sayfanın tamamını değil, anestezi paragrafını bulmak isteriz.
2. **Embedding modelinin okuma sınırı var:** `all-MiniLM-L6-v2` bir metnin sadece ilk **256 token**'ını okur, **gerisini sessizce atar** (hata vermez).

> **Kavram — Token:** Modelin metni okurken kullandığı birim. Kısa, yaygın kelimeler genelde 1 token'dır; uzun veya tıbbi kelimeler birkaç parçaya bölünür (örn. "arthroplasty" → birkaç token). Bu yüzden token sayısı kelime sayısından fazladır.

**İki ayar:**
- **Parça boyutu (chunk size):** Her parçanın uzunluğu. Çok küçük → bağlam kaybolur. Çok büyük → konular karışır ve token sınırı aşılır.
- **Örtüşme (overlap):** Yan yana parçaların ortak paylaştığı kelime sayısı. Bir cümle iki parçanın sınırında kesilirse en az bir parçada tam haliyle bulunsun diye.

```text
Metin:    [──────────────────────────────────────────]
Parça 1:  [──────────────]
Parça 2:             [──────────────]     ← örtüşme
Parça 3:                        [──────────────]
```

### Deney 3: Parça boyutu ve token sınırı (`06_chunking_experiment.py`)

Temiz metin: 1.239 kelime. Model token sınırı: 256.

| Parça boyutu | Örtüşme | Parça sayısı | En uzun parça | Sınırı aşan |
|---|---|---|---|---|
| 100 kelime | 20 | 16 | 205 token | 0 |
| 150 kelime | 30 | 11 | 274 token | 1 |
| 200 kelime | 40 | 8 | 280 token | 1 |
| 400 kelime | 80 | 4 | 504 token | 4 |

- **Sınırı aşmak sessiz bir hata:** 400 kelimelik parçalarda 4 parçanın hepsi uzundu ve her birinin yaklaşık yarısı hiç vektöre dönüştürülmedi. Tek belirti gözden kolayca kaçan bir uyarıydı: `Token indices sequence length is longer than the specified maximum sequence length for this model (274 > 256)`.
- **Kelime başına yaklaşık 1,35 token** düştü, çünkü tıbbi terimler birkaç token'a bölünüyor. 256 token ≈ 180–190 kelime, ama yoğun parçalar 150 kelimede bile sınırı aştı.
- **Örtüşme çalışıyor:** 1. parçanın son 30 kelimesi 2. parçanın ilk 30 kelimesiyle aynıydı.
- **Kelimeye göre kesmek cümleleri bölüyor:** 1. parça "You will not feel any pain during" diye bitti. Örtüşme sayesinde cümlenin tamamı 2. parçada vardı.

### Deney 4: Üç parçalama yöntemi (`08b_chunking_methods_compare.py`)

Her soru için doğru parça **nesnel olarak** tanımlandı: sayfadaki bir **anahtar cümleyi içeren** parça (örn. "You will not feel any pain during the surgery"). Böylece "doğru mu?" kararı göze göre değil, kurala göre verildi.

Üç yöntem:
- **A) Düz kelime:** Bütün sayfa ~120 kelimelik parçalara bölündü.
- **B) Bölümlere göre:** Önce bölüm başlıklarına (Description, Risks, Before the Procedure...) göre ayrıldı, sonra parçalandı. Başlık sadece metadata'da tutuldu.
- **C) Bölüm + başlık:** B ile aynı, ama vektöre dönüştürülen metnin başına "Knee joint replacement - <Bölüm>:" eklendi.

| Soru | A) Düz kelime | B) Bölümlere göre | C) Bölüm + başlık |
|---|---|---|---|
| Will I feel pain during the surgery? | 2. | **1.** | **1.** |
| Why is knee replacement surgery done? | **1.** | 3. | **1.** |
| What should I do two weeks before surgery? | 6. | **3.** | 4. |
| What is the artificial knee joint made of? | 2. | **1.** | 2. |
| **Recall@1** | 1/4 | **2/4** | **2/4** |
| **Recall@3** | 3/4 | **4/4** | 3/4 |

> **Kavram — Recall@K:** "Doğru parça ilk K sonuç içinde mi?" sorusunun oranı. Recall@1 = doğru parça 1. sırada mı; Recall@3 = ilk 3'te mi. LLM sadece ilk K parçayı göreceği için, doğru parça ilk K'da değilse doğru cevap üretilemez.

- **B (bölümlere göre) en iyisiydi:** Dört sorunun hepsinde doğru parça ilk 3'teydi. A'da bir doğru parça 6. sıradaydı; K = 3 ile LLM'e hiç ulaşmazdı.
- **C (başlık eklemek) karışık sonuç verdi:** "Why" sorusunu düzeltti (3. → 1.) ama diğer ikisini biraz kötüleştirdi. Muhtemel sebep: her parçaya aynı sayfa başlığını eklemek parçaları birbirine daha benzer yapıyor.

### Karar
- **Önce bölüm başlıklarına göre ayır, sonra ~120 kelimelik parçalara böl, 25 kelime örtüşme kullan.**
- **Her parçanın ≤ 256 token olduğunu kontrol et** (modelin kendi tokenizer'ıyla say). Daha güvenli bir alternatif, parçaları kelimeye göre değil doğrudan token'a göre boyutlandırmak.
- **Tam soru setinde denenecek iyileştirmeler:** cümle sınırından bölmek; sadece bölüm adını başlık olarak eklemek.
- Embedding modeli değişirse token sınırı da değişir (`all-mpnet-base-v2`: 384, `multi-qa-MiniLM-L6-cos-v1`: 512); parça boyutu yeniden kontrol edilmeli.

## 5. Embedding

**Seçim:** sentence-transformers kütüphanesi, `all-MiniLM-L6-v2` modeli (geçici). Aday: `all-mpnet-base-v2`.

> **Kavram — Embedding:** Bir metni anlamını taşıyan bir sayı listesine (**vektör**) çevirmek. Anlamca benzer metinlerin vektörleri birbirine yakın olur, kelimeleri farklı olsa bile. Örneğin "Ameliyatta acı duyar mıyım?" ile "Anestezi sayesinde ağrı hissetmezsiniz" kelime olarak çok farklı ama vektörleri yakındır.
>
> **Kavram — Benzerlik skoru (cosine similarity):** İki vektörün ne kadar aynı yönü gösterdiğini ölçer. 1'e yakın = çok benzer, 0 civarı = ilgisiz.

- **1. hafta bulgusu** (`01_embedding_experiment.ipynb`): Soruyla neredeyse hiç ortak kelimesi olmayan bir parça en yüksek skoru aldı (0,59); ilgisiz bir cümle −0,01 aldı; konuyla ilgili ama cevap vermeyen parçalar doğru parçaya yakın skor aldı (0,53, 0,51). Yani **eşik değeri** (aşağıda) kritik.

### Deney 5: Üç model (`07_embedding_models_experiment.py`)

MedlinePlus sayfasından 13 parça; 3 cevaplanabilir ve 2 cevaplanamaz soru.

> **Kavram — GAP (aralık):** Cevaplanabilir sorulardaki en düşük skor ile cevaplanamaz sorulardaki en yüksek skor arasındaki fark. Büyük GAP = "cevap var" ile "cevap yok" arasına bir çizgi (eşik) çekmek daha kolay.

| Model | Açıklama | Vektör boyutu | Token sınırı | Yükleme* | 13 parçayı kodlama |
|---|---|---|---|---|---|
| all-MiniLM-L6-v2 | Şu an kullandığımız; küçük, genel amaçlı | 384 | 256 | 3,2 sn | 0,24 sn |
| multi-qa-MiniLM-L6-cos-v1 | Aynı boyut; soru → cevap çiftleriyle eğitilmiş | 384 | 512 | 16,3 sn | 0,16 sn |
| all-mpnet-base-v2 | Daha büyük (~420 MB), genel amaçlı | 768 | 384 | 45,8 sn | 1,15 sn |

\*Yükleme süreleri ilk indirmeyi de içeriyor (MiniLM zaten indirilmişti).

| Model | En düşük cevaplanabilir | En yüksek cevaplanamaz | GAP |
|---|---|---|---|
| all-MiniLM-L6-v2 | 0,63 | 0,43 | **0,20** |
| multi-qa-MiniLM-L6-cos-v1 | 0,65 | 0,46 | 0,19 |
| all-mpnet-base-v2 | 0,63 | 0,46 | 0,16 |

### Gelen parçaların kontrolü (`07b_check_chunks.py`)

İki soru için ilk 3 parçanın **tam metni** okundu:
- **"Will I feel pain during the surgery?"**: MiniLM 1. sıraya yanlış bir parça koydu (0,63; ağrının ameliyat *sebebi* olmasından bahsediyor), doğru parça 2. sıradaydı (0,62). mpnet doğru parçayı 1. sıraya koydu (0,72).
- **"Why is knee replacement surgery done?"**: Bütün modeller doğruydu. Parça "The surgery takes about 2 hours" diye başlıyor ama "Why the Procedure is Performed" bölümünü içeriyor. (Parçayı ilk birkaç kelimesine bakarak değerlendirmek yanıltıcıydı. Doğruluk tam metne bakarak kontrol edilmeli.)

| | Recall@1 | Recall@3 |
|---|---|---|
| all-MiniLM-L6-v2 | 1/2 | 2/2 |
| all-mpnet-base-v2 | 2/2 | 2/2 |

### Bulgular
1. **Büyük model otomatik olarak daha iyi değil:** En büyük GAP küçük modeldeydi.
2. **mpnet bu küçük testte 1. sırada daha isabetliydi.**
3. **GAP tek başına yetmiyor:** Bir model yanlış parçayı yüksek skorla getirebilir. Modeller **Recall@K** ile de karşılaştırılmalı.
4. **Zor soru tipi:** "How much does knee replacement cost in Turkey?" sorusu konuyla ilgili ama cevabı belgelerde yok, ve her modelde 0,43–0,46 aldı ("What is the capital of France?" ≈ 0). Bu tür sorular yüzünden eşik muhtemelen 0,50 civarında olmak zorunda kalacak.
5. **Test küçük** (bir sayfa, beş soru); 0,20 ile 0,19 arasındaki fark anlamlı değil.

### Karar
- **Şimdilik `all-MiniLM-L6-v2` ile devam** (en büyük GAP, en hızlı, doğru parça ilk 3'te).
- **`all-mpnet-base-v2` ekibin soru setinde denenecek;** 20–40 sayfa için hız sorun değil.
- **Son karar:** değerlendirme soru setinde Recall@1, Recall@5 ve GAP'e göre verilecek. Bunun için her cevaplanabilir soruya cevabın bulunduğu **URL ve bölüm** yazılmalı.
- **Dil notu:** Model yalnızca İngilizce. Türkçe soru gerekirse çok dilli bir model (örn. `paraphrase-multilingual-MiniLM-L12-v2`) gerekir; veritabanı yeniden oluşturulmalı ve eşik yeniden ayarlanmalı.
- **Kod notu:** sentence-transformers'ın güncel sürümünde `get_sentence_embedding_dimension()` fonksiyonunun adı `get_embedding_dimension()` oldu.

## 6. Vektör Veritabanı

**Seçim:** ChromaDB, cosine benzerliğiyle (geçici; takım onayı bekleniyor).

> **Kavram — Vektör veritabanı:** Parçaların vektörlerini saklayan ve bir soru vektörüne en yakın vektörleri hızlıca bulan veritabanı. Normal veritabanı "tam eşleşme" arar; vektör veritabanı "anlamca en yakın"ı arar.

### Karşılaştırma (1. hafta)

| Özellik | ChromaDB | PostgreSQL + pgvector |
|---|---|---|
| Kurulum | `pip install chromadb` | Önce PostgreSQL sunucusu, sonra eklenti |
| Python'dan kullanım | Basit komutlar (`add`, `query`) | SQL sorguları, ek bağlantı kütüphanesi |
| Vektör arama | Var; her vektörle birlikte metni ve metadata'yı saklıyor | Var; büyük verilerde çok güçlü |
| Ayrı veritabanı gerekir mi | Hayır | Evet (PostgreSQL) |
| Docker | Uygulamanın içinde çalışıyor, ayrı servis yok | Ayrı PostgreSQL servisi |
| Güçlü olduğu yer | Prototip, küçük ve orta veri | Büyük, çok kullanıcılı sistemler; vektörlerin yanında başka veri saklamak |

**ChromaDB'nin sebepleri:** Verimiz küçük (20–40 sayfadan birkaç yüz parça); hızlı prototip gerekiyor (M2); daha az servis, tek `docker-compose up`'ı kolaylaştırıyor; planlanan robot arayüzünü engellemiyor.
**pgvector'a ne zaman geçilir:** Çok kullanıcı veya cihaz, çok daha büyük veri, ya da başka veri saklama ihtiyacı (örn. sohbet kayıtları). Veritabanı kodunun tamamı `src/retrieval/` içinde olacak; geçiş sadece o klasörü etkiler.

### Deney 6: Gerçek parçalar + metadata (`08_chromadb_real_chunks.py`)

- Gerçek MedlinePlus parçaları, bölümlere göre parçalama ile 14 parça, ayrı bir koleksiyona (`medlineplus_test`) kaydedildi. 1. haftanın demo verisi bozulmadı.
- **Cosine benzerliği koleksiyon oluşturulurken açıkça belirtildi:** `metadata={"hnsw:space": "cosine"}`. Böylece benzerlik = 1 − mesafe olur. (Belirtilmezse ChromaDB başka bir mesafe ölçüsü kullanır ve skorlar karşılaştırılamaz.)
- Her arama sonucu hazır bir kaynak satırıyla geldi, örneğin:
  `CITATION: MedlinePlus, "Knee joint replacement", section "Description" - https://medlineplus.gov/ency/article/002974.htm`

> **Kavram — Metadata:** Parçanın kendisi değil, parça hakkındaki bilgi: hangi siteden, hangi sayfadan, hangi bölümden geldiği. Cevapta kaynak gösterebilmek (citation) için metadata şart.

### Metadata yapısı (her parça için)

```text
id                 medlineplus-002974-003   (kaynak + sayfa no + sıra → her çalıştırmada aynı kalır)
url                https://medlineplus.gov/ency/article/002974.htm
title              Knee joint replacement
source             MedlinePlus
section            Why the Procedure is Performed
chunk_in_section   0
(+ kaynak listesinden: date_accessed, last_updated)
```

Veritabanı `chroma_db/` klasöründe durur, GitHub'a yüklenmez (`.gitignore`) ve belgelerden her zaman yeniden oluşturulabilir.

## 7. Getirme (Retrieval) Ayarları

> **Kavram — Top-K:** Bir soru için veritabanından kaç parça getirileceği. LLM sadece bu K parçayı görür.
>
> **Kavram — Eşik değeri (threshold):** En iyi parçanın skoru bu değerin altındaysa sistem "Bilmiyorum" der. Çok yüksek eşik → cevabı olan soruları da reddeder. Çok düşük eşik → cevabı olmayan sorulara da cevap uydurmaya çalışır.

- **Top-K = 5.** En iyi parçalama yönteminde bile bir doğru parça 3. sıradaydı (C yönteminde 4.); K = 3 fazla dar. (Proje tanımı K'yı belirtmiyor.)
- **Eşik:** henüz belirlenmedi. Şimdiye kadar görülenler: cevaplanabilir sorular 0,62–0,72; konuyla ilgili ama cevapsız ("Türkiye'de maliyet") 0,43–0,46; konu dışı ("Fransa'nın başkenti") ≈ 0. Değer değerlendirme soru setinde seçilecek; embedding modeli değişirse yeniden ayarlanmalı.

## 8. LLM (Büyük Dil Modeli)

Proje tanımı, aynı 200 soruda bir **yerel** ve bir **hosted** modelin karşılaştırılmasını istiyor (cevap doğruluğu, kaynak doğruluğu, doğru reddetme).

> **Kavram — Yerel (local) model:** Kendi bilgisayarımızda çalışan model. Ücretsiz, internet gerektirmez, veri bilgisayardan çıkmaz.
>
> **Kavram — Hosted model:** Bir şirketin sunucusunda çalışan, internet üzerinden API ile kullandığımız model. Genelde daha güçlü ama ücretli.

### Yerel model

**Seçim:** Ollama + `llama3.2` (3 milyar parametre, ~2 GB).

- **Ollama** modelleri kendi bilgisayarımızda çalıştırır. Hesap açmanı isterse "No thanks, I'll use Ollama locally" seç; hesap ücretsiz ama gerekli değil. Adında "cloud" geçen modelleri kullanma (onlar Ollama'nın sunucularında çalışır, yerel değil).
- **Ölçülen hız:**

| Bilgisayar | Ekran kartı | Üretim hızı | Kısa cevap |
|---|---|---|---|
| Eski laptop | RTX 3050 Laptop, 4 GB (sürücü 511.65 → 617.14 güncellendi) | ~51 token/sn | ~3,7 sn |
| Yeni laptop | RTX 4060 Laptop, 8 GB (sürücü 610.60) | ~87–99 token/sn | ~1,1 sn |

- `ollama ps` yeni laptopta **%100 GPU** kullanıldığını doğruladı.
- **İlk çağrı yavaş:** İlk soruda sadece prompt değerlendirmesi 27 sn sürdü (ekran kartı ısınıyordu); sonraki çağrılar ~1 sn. **Demodan önce modeli bir soruyla ısıtın.**
- 8 GB ekran kartı belleğiyle daha büyük bir model (~8 milyar parametre) ileride denenebilir.

### Hosted model

**Durum:** Seçilmedi. API üzerinden kullanılacak. API anahtarı `.env` dosyasında tutulacak (**asla GitHub'a yüklenmez**); depoda boş bir `.env.example` şablonu olacak. 200 soruluk bir çalıştırmanın tahmini maliyeti: küçük modellerle birkaç sent, en güçlü modellerle yaklaşık 1–2 USD.

## 9. Güvenlik Kuralı (1. hafta)

Proje tanımı, ilaç ve acil durum sorularının sabit bir mesajla **her zaman** reddedilmesini istiyor.

- 1. hafta deneyleri (`03_rag_experiment.ipynb`) gösterdi ki benzerlik eşiği tehlikeli soruları durduramıyor. Veritabanında bir ilaç parçası varken LLM "Can I take ibuprofen…?" sorusunu o parçadan cevapladı. **Bu yüzden güvenlik kontrolü getirme ve LLM'den önce çalışmalı.**
- Şu anki sürüm (v0): anahtar kelime listesi. **Bilinen zayıflık:** marka isimleri ("Advil"), yazım hataları ve dolaylı ifadeler kontrolü atlatıyor. Ayrıca LLM parçadaki ifadeyi esnetti ("may be given" → "you can take").
- **İleriki seçenekler:** daha uzun bir liste, bilinen tehlikeli sorularla embedding tabanlı karşılaştırma, LLM tabanlı sınıflandırıcı, ya da bunların birleşimi.
- Streamlit demosunda gözlenen: Model bazen reddetme mesajına parça numarası ekliyor ("I don't know… [2]"). Prompt sıkılaştırılmalı ya da numara kodda silinmeli.

## 10. Web Arayüzü

**Seçim:** Streamlit. Sadece Python ile yazılan, hazır sohbet bileşenleri olan web sayfaları. 1. haftanın demosu (`04_streamlit_demo.py`) prototipi bir sohbet ekranına bağlıyor ve getirilen parçaları kaynaklarıyla gösteriyor. Arayüz (`app/`) sistem mantığından (`src/`) ayrı tutuluyor; böylece başka bir arayüz (örn. robot) aynı mantığı kullanabilir.

## 11. Paketleme (Docker Compose)

> **Kavram — Docker:** Uygulamayı ve ihtiyaç duyduğu her şeyi (Python sürümü, kütüphaneler) tek bir "konteyner"e koyar, böylece her bilgisayarda aynı şekilde çalışır. **Docker Compose** birden fazla konteyneri tek komutla birlikte başlatır.

**Seçim:** Docker Compose, projenin sonunda yazılacak. Jüri her şeyi tek bir `docker-compose up` komutuyla başlatabilmeli. Planlanan konteynerler: uygulama (Python, Streamlit, RAG kodu, ChromaDB) ve Ollama. ChromaDB uygulamanın içinde çalıştığı için ayrı veritabanı konteynerine gerek yok. Docker dosyaları `docker/` klasörüne gidecek.

## 12. Soru Dili

**Seçim:** İngilizce (geçici; danışman onayı bekleniyor). Proje tanımı dili belirtmiyor; bütün kaynaklar İngilizce. Demonun başında jüriye sistemin İngilizce çalıştığı söylenmeli.

## 13. Sorumlu Veri Toplama

> **Kavram — robots.txt:** Sitelerin "otomatik programlar hangi sayfalarıma girebilir" kurallarını yazdığı dosya (örn. `https://www.nhs.uk/robots.txt`). Uymak yasal ve etik bir nezakettir.

- **Kendimizi tanıtmak:** Her istekte açıklayıcı bir `User-Agent` ("CiteOrAbstain student project (educational use)").
- **Az ve yavaş istek:** İstekler arasında bekleme (örn. 2 sn); her sayfa **bir kez** indirilip `data/raw/` klasörüne kaydedilir; sonraki çalıştırmalar yerel kopyayı kullanır.
- **robots.txt'ye uymak:** Her site için kontrol edilir. NHS sayfalarımıza izin verdi. NIAMS'ta kontrol SSL sertifika hatasıyla başarısız oldu, çünkü Python'un `RobotFileParser`'ı `requests` ile aynı sertifika listesini kullanmıyor. Çözüm: robots.txt'yi `requests` ile indirip `RobotFileParser.parse()` ile okumak.
- **Kullanım koşulları:** Ham metinler depoda saklanacak. Depo gizli olduğu sürece sorun yok. Depo herkese açılmadan önce her kaynağın kullanım koşulları kontrol edilmeli (örn. MedlinePlus ansiklopedi sayfaları yeniden yayınlanması kısıtlı olabilen A.D.A.M. içeriği barındırıyor; NHS'in kendi koşulları var).
- **Gerçek hasta verisi asla kullanılmaz** (proje şartı); sadece herkese açık hasta bilgilendirme sayfaları.

## 14. İlk Getirme Prototipi (ortak kodlama günü planı)

```text
URL listesi (kaynak listesi)
   ↓  requests (ham bayt) + trafilatura
Temiz metin  →  data/raw/                 (bir kez indirilir, kaydedilir)
   ↓  bölümlere ayır → ~120 kelime / 25 örtüşme, ≤ 256 token
Parçalar + metadata  →  data/processed/chunks.jsonl
   ↓  all-MiniLM-L6-v2
ChromaDB (cosine)  →  chroma_db/          (GitHub'da yok, yeniden oluşturulabilir)
   ↓
Soru → en benzer 5 parça + kaynak bilgisi
```

> **Kavram — JSONL:** Her satırı ayrı bir JSON kaydı olan metin dosyası. Burada her satır bir parça (metin + metadata). Okuması ve elle kontrol etmesi kolay.

| Dosya | Görevi |
|---|---|
| `src/ingestion/extract.py` | URL → temiz metin, `data/raw/`'a kaydet; son adresi, metin uzunluğunu, gürültü satırlarını kontrol et |
| `src/ingestion/chunk.py` | Metin → bölümler → parçalar + metadata; token kontrolü |
| `src/retrieval/index.py` | Parçalar → vektörler → ChromaDB |
| `src/retrieval/search.py` | Soru → en benzer 5 parça + kaynak satırı |

**Test:** İlk 20–30 değerlendirme sorusunda Recall@5. Cevaplanamaz sorular için en yüksek skorlar kaydedilecek (ileride eşik ayarı için). Bu hafta LLM'e gerek yok; ilk hedef doğru belgeyi getirmek.

`notebooks/` içindeki `05`–`09` deney dosyaları bu kodun ilk halidir.

## 15. Gelecek: Robot

Robot yeni bir arayüz olacak: sesli soruyu metne çevirip aynı RAG sistemine gönderecek ve cevabı sesli okuyacak. Seçtiğimiz teknolojiler bunu engellemiyor (ChromaDB küçük cihazlar için yeterince hafif). Robot için önemli olanlar: RAG mantığını arayüzden bağımsız tutmak, cevap hızı ve dil desteği.

---

## Deney Listesi

| Dosya | Konu | Hafta |
|---|---|---|
| `01_embedding_experiment.ipynb` | Embedding ve benzerlik skorları | 1 |
| `02_chromadb_experiment.ipynb` | İlk ChromaDB kullanımı (örnek cümleler) | 1 |
| `03_rag_experiment.ipynb` | İlk RAG prototipi, kaynak gösterme, çekimser kalma, güvenlik kuralı | 1 |
| `04_streamlit_demo.py` | Streamlit sohbet demosu | 1 |
| `05_text_extraction_experiment.py` | BeautifulSoup vs trafilatura | 2 |
| `06_chunking_experiment.py` | Parça boyutu, örtüşme, token sınırı; encoding düzeltmesi | 2 |
| `07_embedding_models_experiment.py` | Üç embedding modeli, GAP | 2 |
| `07b_check_chunks.py` | Getirilen parçaların tam metin kontrolü, Recall@K | 2 |
| `08_chromadb_real_chunks.py` | Gerçek parçalar + metadata ile ChromaDB | 2 |
| `08b_chunking_methods_compare.py` | Üç parçalama yöntemi, nesnel sıralama | 2 |
| `09_other_sources_test.py` | NHS ve NIH NIAMS'tan metin çıkarma, robots.txt | 2 |

## Takım / Danışman İçin Açık Sorular

1. Vektör veritabanı olarak ChromaDB'nin onaylanması.
2. Soru dilinin İngilizce olmasının onaylanması.
3. Hosted model sağlayıcısının seçilmesi.
4. Anahtar kelime listesinden sonraki güvenlik kuralı yaklaşımı.
5. Branch + Pull Request kurallarının ve `requirements-lock.txt` eklenmesinin onaylanması.
6. NIAMS'ın doğru diz protezi sayfasının bulunması; NHS adreslerinin `/tests-and-treatments/...` olarak güncellenmesi.
7. Depo herkese açılmadan önce kullanım koşullarının kontrol edilmesi.

## Kısa Sözlük

| Terim | Kısaca |
|---|---|
| RAG | Belgelerden bilgi getirip LLM'e cevap yazdırma yöntemi |
| Chunk (parça) | Belgenin küçük metin parçası |
| Overlap (örtüşme) | Yan yana parçaların ortak kelimeleri |
| Token | Modelin okuma birimi (kelime veya kelime parçası) |
| Embedding | Metni anlamını taşıyan sayı listesine (vektör) çevirme |
| Cosine similarity | İki vektörün benzerlik skoru (1 = çok benzer, 0 = ilgisiz) |
| Top-K | Getirilen parça sayısı |
| Threshold (eşik) | Altında "Bilmiyorum" denen skor |
| Recall@K | Doğru parçanın ilk K sonuçta olma oranı |
| GAP | Cevaplanabilir ve cevaplanamaz soruların skor farkı |
| Metadata | Parçanın kaynak bilgisi (URL, başlık, bölüm) |
| Citation | Cevapta kaynağı gösterme |
| Abstention | Cevap yoksa çekimser kalma ("Bilmiyorum") |
| Hallucination | LLM'in kaynakta olmayan bilgiyi uydurması |
| Branch / PR | Ayrı çalışma dalı / dalı `main`'e ekleme isteği |
| venv | Projeye özel Python ortamı |
