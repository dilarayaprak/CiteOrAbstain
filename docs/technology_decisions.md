# Technology Decisions

Bu belge, CiteOrAbstain projesinde kullanılacak teknolojileri, verilen kararları ve gerekçelerini içerir. Kararlar 1. haftadaki araştırma ve deneylere dayanmaktadır. Deneylerin kodu ve sonuçları `notebooks/` klasöründedir.

Hazırlayan: Dilara Yaprak — Son güncelleme: Ekim 2026 (1. hafta)

## Karar Özeti

| Alan | Seçim | Durum |
|---|---|---|
| Programming Language | Python 3.12 | Kesin |
| Embedding | sentence-transformers, `all-MiniLM-L6-v2` | Geçici (dil kararına bağlı) |
| Vector Database | ChromaDB | Geçici (ekip onayı bekleniyor) |
| LLM (local) | Ollama + `llama3.2` (3B) | Geçici |
| LLM (hosted) | Henüz seçilmedi | Açık |
| Web UI | Streamlit | Kesin |
| Containerization | Docker Compose | Kesin (finalde yazılacak) |
| Version Control | GitHub | Kesin |
| Question Language | İngilizce | Geçici (danışman onayı bekleniyor) |

**Durumların anlamı:** *Kesin* = değişmesi beklenmiyor. *Geçici* = şimdilik bununla ilerliyoruz, gerekirse değişebilir. *Açık* = henüz karar verilmedi.

---

## Programming Language

**Seçim:** Python 3.12

- Proje dokümanı Python öneriyor. Embedding, vektör veritabanı, LLM ve Streamlit kütüphanelerinin hepsi Python ile çalışıyor.
- **Neden 3.12?** Daha yeni olan 3.14, PyTorch ve onnxruntime gibi ağır kütüphanelerle uyumluluk riski taşıyor. 3.12 bu kütüphanelerin hepsiyle sorunsuz çalışıyor.
- Ekipteki herkes aynı sürümü kullanacak. Finaldeki Docker ortamı da aynı sürümle kurulacak.
- Kütüphane sürümleri `requirements.txt` içinde sabitlendi (ör. `chromadb==1.5.9`). Böylece herkes birebir aynı sürümleri kurar.

## Embedding

**Seçim:** sentence-transformers kütüphanesi, `all-MiniLM-L6-v2` modeli

- **Görevi:** Pasajları ve soruları anlamını taşıyan sayılara (vektörlere) çevirmek. Bu model her metni 384 sayıya çeviriyor.
- **Neden bu model?** Küçük (yaklaşık 90 MB), hızlı, ücretsiz ve bilgisayarda yerel olarak çalışıyor. İngilizce metinlerde yaygın olarak kullanılıyor.
- **Deney bulguları** (`01_embedding_experiment.ipynb`):
  - Soruyla neredeyse hiç ortak kelimesi olmayan doğru pasaj en yüksek skoru aldı (0.59). Model kelimelere değil anlama bakıyor.
  - Alakasız pasaj sıfıra yakın skor aldı (-0.01). Konu dışı sorularda çekilmek kolay.
  - Konuyla ilgili ama soruyu cevaplamayan pasajlar da yakın skorlar aldı (0.53, 0.51). Eşik seçimi bu yüzden kritik.
- **Not:** Model İngilizce için tasarlandı. Türkçe soru desteği istenirse çok dilli bir modele (ör. `paraphrase-multilingual-MiniLM-L12-v2`) geçilmeli. Bu durumda veritabanı yeniden oluşturulmalı ve eşik yeniden ayarlanmalı.

## Vector Database

**Seçim:** ChromaDB (geçici karar)

**Aday karşılaştırması:**

| Özellik | ChromaDB | PostgreSQL + pgvector |
|---|---|---|
| Kurulum | `pip install chromadb` yeterli | Önce PostgreSQL kurulmalı, sonra eklenti etkinleştirilmeli |
| Python kullanımı | Basit Python komutları (`add`, `query`) | SQL ile sorgu, ek bağlantı kütüphaneleri gerekli |
| Vektör arama | Var, metin ve kaynak bilgisini vektörle birlikte saklıyor | Var, büyük veride çok güçlü |
| Ek veritabanı gerekir mi? | Hayır | Evet (PostgreSQL) |
| Docker | Uygulamanın içinde çalışır, ek servis gerekmez | Ayrı bir PostgreSQL servisi gerekir |
| Güçlü olduğu yer | Prototip, küçük ve orta boy veri | Çok kullanıcılı büyük sistemler, vektörlerin yanında başka veriler de saklamak |

**Gerekçe:**

1. Verimiz küçük: 20-40 sayfadan birkaç yüz pasaj çıkacak.
2. Hızlı bir prototip gerekiyor (M2).
3. Finalde tek `docker-compose up` komutuyla çalışması gerekiyor. Ne kadar az servis, o kadar az sorun.
4. İleride planlanan robot entegrasyonuna engel değil. Robot, aynı RAG sistemine bağlanacak bir arayüz olacak.

**Deney bulguları** (`02_chromadb_experiment.ipynb`):

- Kurulum ve kullanım çok kolaydı. Birkaç satır kodla veri eklendi ve arama yapıldı.
- Veritabanı kalıcı: Jupyter kapatılıp açıldıktan sonra da veriler duruyordu.
- Sonuçlar elle yapılan hesapla birebir aynı çıktı (aynı pasaj iki deneyde de 0.59 aldı).
- Her pasaj, kaynak bilgisiyle birlikte saklandı ve aramada kaynağıyla birlikte geri geldi.

**pgvector'a ne zaman geçilir?** Çok sayıda kullanıcı ya da cihaz olursa, veri çok büyürse ya da vektörlerin yanında başka veriler (sohbet kayıtları gibi) saklamak gerekirse. Veritabanı kodu `src/retrieval/` klasöründe toplanacağı için geçiş sadece bu klasörü etkiler.

**Teknik not:** Veritabanı `chroma_db/` klasöründe tutulur ve GitHub'a gönderilmez (`.gitignore`). Belgelerden her zaman yeniden oluşturulabilir.

## LLM

PDF, yerel bir model ile sunucuda barındırılan (hosted) bir modelin karşılaştırılmasını **zorunlu** tutuyor: aynı 200 soru iki modele de sorulacak ve doğru cevap, doğru kaynak ve doğru ret oranları karşılaştırılacak.

### Local model

**Seçim:** Ollama + `llama3.2` (3 milyar parametre, yaklaşık 2 GB)

- **Ollama:** Modelleri bilgisayarda yerel olarak indirip çalıştıran ücretsiz bir program. İnternet gerektirmez, veri bilgisayardan çıkmaz.
- **Neden bu model?** Test bilgisayarındaki ekran kartının (NVIDIA RTX 3050 Laptop, 4 GB bellek) belleğine sığıyor. İngilizcede güçlü.
- **Ölçülen performans:** Saniyede yaklaşık 51 token. Kısa bir cevap yaklaşık 4 saniyede geliyor.
- **Önemli:** Ekran kartının kullanılabilmesi için güncel NVIDIA sürücüsü gerekiyor (eski 511.65 sürücüsü 617.14'e güncellendi).

### Hosted model

**Durum:** Henüz seçilmedi.

- Bir şirketin sunucusunda çalışan, API üzerinden kullanılan bir model olacak (ör. OpenAI, Google, Anthropic).
- **Maliyet tahmini:** Kullanım başına ücretlendiriliyor. 200 soruluk bir test, küçük modellerle birkaç sent, en güçlü modellerle yaklaşık 1-2 dolar tutuyor. Proje boyunca toplam maliyetin düşük kalması bekleniyor. Bazı sağlayıcılar ücretsiz deneme kredisi sunuyor.
- **Güvenlik:** API anahtarı `.env` dosyasında tutulacak ve GitHub'a gönderilmeyecek (`.gitignore`). Repoda sadece değerleri boş bir `.env.example` şablonu olacak.

## Web UI

**Seçim:** Streamlit

- Sadece Python ile web arayüzü yapmayı sağlıyor. HTML, CSS veya JavaScript bilmek gerekmiyor. Hazır sohbet bileşenleri var.
- **Deney:** `04_streamlit_demo.py` ile RAG prototipi bir sohbet ekranına bağlandı ve sorunsuz çalıştı. Kullanıcı cevabın altında, cevabın dayandığı pasajları kaynaklarıyla birlikte görebiliyor.
- Arayüz kodu (`app/`) ile sistemin mantığı (`src/`) ayrı tutulacak. Böylece ileride robot gibi başka bir arayüz de aynı sistemi kullanabilir.

## Containerization

**Seçim:** Docker Compose (finalde yazılacak)

- PDF, projenin jüri önünde **tek bir `docker-compose up` komutuyla** çalışmasını istiyor.
- Planlanan yapı:
  - **Uygulama container'ı:** Python, Streamlit, RAG kodu ve ChromaDB
  - **Ollama container'ı:** Yerel LLM
- ChromaDB uygulamanın içinde çalıştığı için ayrı bir veritabanı container'ına gerek yok.
- Docker dosyaları `docker/` klasörüne yazılacak.

## Version Control

**Seçim:** GitHub — `dilarayaprak/CiteOrAbstain` (private)

- Ekip üyeleri collaborator olarak eklendi. Herkes kendi hesabından commit atacak, böylece katkılar görünür olacak.
- Klasör yapısı, PDF'deki dört modülü yansıtıyor: `src/ingestion` (belge işleme), `src/retrieval` (arama), `src/generation` (cevap, kaynak, çekilme), `app` (arayüz).
- `.gitignore` ile venv, API anahtarları, veritabanı ve model dosyaları repoya girmiyor.
- Kurulum adımları README'de.

---

## Safety Rule

PDF, ilaç ve acil durum sorularının **her zaman** sabit bir mesajla reddedilmesini istiyor.

**Deney bulguları** (`03_rag_experiment.ipynb`):

- Benzerlik eşiği tehlikeli soruları tek başına durduramıyor. İlaç dozu sorusu bile 0.46 skor aldı.
- Veritabanında ilaçtan bahseden bir pasaj olduğunda, "İbuprofen alabilir miyim?" sorusuna LLM pasajı kullanarak cevap verdi. Model kurallara uydu, ama ilaç sorusunu cevaplamış oldu.
- **Sonuç:** Güvenlik kontrolü, arama ve LLM'den **önce** çalışan ayrı bir katman olmalı.

**Mevcut durum (v0):** Anahtar kelime listesine dayalı bir kural yazıldı ve çalışıyor.

**Bilinen zayıflıklar:**

- Listede olmayan marka adları (ör. "Advil"), yazım hataları ve dolaylı ifadeler kuralı aşabiliyor.
- Bu durumda LLM kendi hafızasını kullanabiliyor ve pasajı abartabiliyor ("verilebilir" yerine "alabilirsiniz").

**2. hafta için seçenekler:** Listeyi genişletmek, embedding tabanlı kontrol (gelen soruyu bilinen tehlikeli soru örnekleriyle karşılaştırmak), LLM tabanlı sınıflandırma ya da bunların birleşimi.

## Retrieval Parameters

- **Top-K:** Deneylerde K=3 kullanıldı. PDF'de bir değer belirtilmemiş. Deneyler K'nın 1 olmaması gerektiğini gösterdi: bir soruda en yüksek skorlu pasaj yanlıştı, doğru cevap ikinci sıradaydı ve LLM doğru pasajı seçebildi. Kesin değer test sonuçlarına göre belirlenecek.
- **Eşik (threshold):** Henüz belirlenmedi. Cevaplanabilir bir soruda en yüksek skor 0.68, alakasız bir soruda 0.09 oldu. Kesin değer, 200 soruluk test seti üzerinde denenerek seçilecek. Model değişirse eşik yeniden ayarlanmalı.

## Question Language

**Seçim:** İngilizce (geçici, danışman onayı bekleniyor)

- PDF'de soruların dili belirtilmemiş. Kaynaklar (NHS, MedlinePlus, NIH NIAMS) İngilizce.
- Final demosunda jüriye sistemin İngilizce çalıştığı baştan belirtilmeli.

## Future: Robot

- Robot, sistemin yeni bir arayüzü olacak: sesli soruyu yazıya çevirip aynı RAG sistemine soracak ve cevabı sesli okuyacak.
- Seçilen teknolojiler robot entegrasyonuna engel değil. ChromaDB hafif olduğu için küçük cihazlarda çalışmaya da uygun.
- Robot için asıl önemli konular: RAG mantığının arayüzden bağımsız tutulması, cevap hızı ve dil desteği.

---

## Perşembe Toplantısında Karar Verilecekler

1. ChromaDB'nin onaylanması
2. Soruların dili (danışmana sorulacak)
3. Hosted model sağlayıcısı
4. Güvenlik kuralının 2. haftadaki yaklaşımı
