# CiteOrAbstain — Kurulum ve Çalışma Rehberi

Bu rehber, projeyi kendi bilgisayarında **sıfırdan** kurman ve ekiple birlikte çalışman için hazırlandı. Hiçbir ön bilgi gerektirmez. Her adımda **ne yaptığımızı**, **neden yaptığımızı** ve **ekranda ne göreceğini** anlatıyor.

Rehber Windows için yazıldı. Komutları **PowerShell**'e yazacaksın: Başlat menüsüne `PowerShell` yaz ve aç.

> **Altın kural:** Komutları **tek tek** kopyala, yapıştır ve Enter'a bas. Birden fazla satırı aynı anda yapıştırırsan komutlar birbirine yapışıp hata verebilir.

---

## Ne zaman ne yapmalısın?

| Ne zaman | Bölümler |
|---|---|
| **Şimdi (1. hafta)** | Bölüm 1 yeterli. Dosyalarını tarayıcıdan yükleyebilirsin (Bölüm 8). |
| **2. haftadan önce** | Bölüm 2, 3, 4, 5 ve 6 |
| **Her çalışmada** | Bölüm 7 ve 8 |

---

## Bölüm 1 — GitHub hesabı ve davet

**Ne:** Projenin internetteki ortak deposu GitHub'da duruyor: `github.com/dilarayaprak/CiteOrAbstain`

**Neden:** Üçümüz de kendi bilgisayarımızda çalışacağız, ama işler GitHub'da birleşecek. Herkesin **kendi hesabıyla** katkı yapması önemli. Hocamız GitHub geçmişinden kimin neye katkı yaptığını görebiliyor.

1. Hesabın yoksa https://github.com/signup adresinden aç. Kullanıcı adı CV'nde de görünebilir, sade bir şey seç.
2. Dilara'nın gönderdiği davet e-postana gelecek: **"[GitHub] dilarayaprak invited you to dilarayaprak/CiteOrAbstain"**. İçindeki **View invitation** butonuna, sonra **Accept invitation**'a tıkla.
   - E-posta gelmediyse **Spam** ve **Promosyonlar** klasörlerine bak.
   - Hâlâ yoksa github.com'a giriş yapıp repo adresine git, davet orada çıkar.
   - Davetin süresi 7 gün sonra doluyor.

> ⚠️ **Hesap bilgilerini kimseyle paylaşma.** Herkes kendi hesabını kullanmalı.

---

## Bölüm 2 — Python ve Git kurulumu

**Ne:**
- **Python 3.12:** Projenin yazıldığı programlama dili.
- **Git:** Dosyalardaki değişiklikleri kaydeden ve GitHub'a gönderen araç.

**Neden 3.12?** Daha yeni sürümler (3.13, 3.14) projede kullandığımız bazı büyük kütüphanelerle sorun çıkarabiliyor. Üçümüz de **aynı sürümü** kullanmalıyız, yoksa "bende çalışıyor, sende çalışmıyor" sorunu yaşanır.

### 2.1 Bilgisayarında ne kurulu, kontrol et

```powershell
py --list
```

```powershell
git --version
```

- Listede `3.12` görüyorsan Python 3.12 zaten kurulu. 2.2'yi atla.
- `git version ...` yazıyorsa Git kurulu. 2.3'ü atla.
- "tanınmıyor" / "not recognized" hatası, o programın kurulu olmadığı anlamına gelir.

> Bilgisayarında başka bir Python sürümü (ör. 3.14) varsa **silme.** 3.12'yi yanına kuracağız. Windows'ta birden fazla sürüm sorunsuz yan yana durabilir.

### 2.2 Python 3.12'yi kur

```powershell
winget install Python.Python.3.12
```

- Kaynak sözleşmesini kabul etmeni isterse `Y` yazıp Enter'a bas.
- Windows "değişiklik yapmasına izin veriyor musunuz?" diye sorarsa **Evet** de.
- Sonunda **"Successfully installed"** yazmalı.

### 2.3 Git'i kur

```powershell
winget install Git.Git
```

### 2.4 PowerShell'i tamamen kapatıp yeniden aç

**Neden:** Yeni kurulan programlar, açık olan PowerShell pencereleri tarafından tanınmaz. **Bütün** PowerShell pencerelerini kapat (sadece sekmeyi değil), sonra yeniden aç ve kontrol et:

```powershell
py -3.12 --version
```

```powershell
git --version
```

İkisi de bir sürüm numarası göstermeli (ör. `Python 3.12.10`).

---

## Bölüm 3 — Git'e kendini tanıt

**Neden:** Git'e yaptığın her kayda (commit) adın ve e-postan yazılır. E-posta, **GitHub hesabındaki e-postayla aynı** olmalı. Yoksa commit'lerin GitHub'da senin profiline bağlanmaz ve katkın görünmez.

Aşağıdaki komutları **tek tek** çalıştır. İlk ikisinde kendi bilgilerini yaz:

```powershell
git config --global user.name "Adın Soyadın"
```

```powershell
git config --global user.email "github-epostan@gmail.com"
```

```powershell
git config --global init.defaultBranch main
```

```powershell
git config --global core.autocrlf true
```

Ne işe yarıyorlar:
- **`user.name` / `user.email`:** Commit'lerinde görünecek ad ve e-posta.
- **`init.defaultBranch main`:** Ana dalın adını GitHub ile uyumlu yapar.
- **`core.autocrlf true`:** Windows ve Mac satır sonlarını farklı yazar. Bu ayar, dokunmadığın dosyaların "değişmiş" görünmesini önler.

Bu komutlar başarılı olunca **hiçbir şey yazmaz**, bu normal. Kontrol etmek için:

```powershell
git config --global --list
```

Listede yazdığın ad ve e-postayı görmelisin.

---

## Bölüm 4 — Projeyi bilgisayarına indir (clone)

**Ne:** GitHub'daki projenin bir kopyasını bilgisayarına indiriyoruz.

**Neden:** Dosyaları kendi bilgisayarında düzenleyip sonra GitHub'a göndereceksin. `git clone`, bilgisayarındaki klasör ile GitHub arasındaki bağlantıyı da otomatik kurar.

**Nereye?** Projeyi **Masaüstü'ne veya Belgeler'e koyma.** Bu klasörler genelde OneDrive ile senkronize edilir ve proje dosyalarıyla sorun çıkarır. Kendi kullanıcı klasöründe bir `Projects` klasörü kullanıyoruz.

Komutları **tek tek** çalıştır:

```powershell
cd $HOME
```

```powershell
mkdir Projects
```

> `Projects` klasörü zaten varsa "already exists" hatası alırsın. Sorun değil, devam et.

```powershell
cd Projects
```

```powershell
git clone https://github.com/dilarayaprak/CiteOrAbstain.git
```

**Ekranda göreceklerin:**
- Bir **GitHub giriş penceresi** açılabilir. Repo gizli (private) olduğu için Git kim olduğunu soruyor. **Sign in with your browser**'a tıkla ve tarayıcıda **Authorize** de. Bu sadece ilk seferde olur.
- "Authentication failed" hatası alırsan Bölüm 9'a bak.

```powershell
cd CiteOrAbstain
```

Satırın başı artık `PS C:\Users\...\Projects\CiteOrAbstain>` olmalı. Bu, proje klasörünün içinde olduğun anlamına gelir.

---

## Bölüm 5 — Sanal ortam (venv) ve kütüphaneler

**Ne:** Projeye özel, izole bir Python ortamı ve projenin ihtiyaç duyduğu kütüphaneler.

**Neden:** Projede büyük kütüphaneler kullanıyoruz (ChromaDB, sentence-transformers, Streamlit...). Bunları bilgisayarın geneline kurarsak başka projelerle karışabilir. **venv**, projeye ait ayrı bir "kutu" açar. Kurduğumuz her şey o kutunun içinde kalır. Kutu GitHub'a gönderilmez, herkes kendi bilgisayarında oluşturur.

### 5.1 venv'i oluştur

```powershell
py -3.12 -m venv venv
```

10-20 saniye sürebilir, sonunda hiçbir şey yazmaz. `py -3.12` kısmı, bilgisayarında başka Python sürümleri olsa bile 3.12'nin kullanılmasını sağlar.

### 5.2 Windows'un script iznini aç

**Neden:** Windows, varsayılan olarak venv'i aktifleştiren script'in çalışmasını engeller. Bu komut, izni sadece senin kullanıcı hesabın için açar ve internetten indirilen imzasız script'leri engellemeye devam eder. Herkesin bir kez yapması gerekiyor.

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Onay sorarsa `Y` de. Hiçbir şey yazmazsa da sorun yok.

### 5.3 venv'i aktifleştir

```powershell
.\venv\Scripts\Activate.ps1
```

Satırın başında **`(venv)`** belirmeli:

```text
(venv) PS C:\Users\...\Projects\CiteOrAbstain>
```

Kontrol et:

```powershell
python --version
```

`Python 3.12.x` yazmalı.

### 5.4 Kütüphaneleri kur

```powershell
python -m pip install --upgrade pip
```

```powershell
python -m pip install -r requirements.txt
```

- `requirements.txt`, projenin ihtiyaç duyduğu kütüphanelerin listesi. Sürümleri sabitlendi, böylece herkes birebir aynı sürümleri kurar.
- **5-15 dakika sürebilir.** Ekranda yüzlerce satır akacak. Bunun sebebi, kütüphanelerin başka kütüphanelere ihtiyaç duyması ve pip'in hepsini otomatik indirmesi.
- Sonunda **"Successfully installed ..."** ile başlayan uzun bir satır görmelisin. Bu yazı birkaç ekran yukarıda kalabilir, yukarı kaydırarak görebilirsin.

> 💡 Hep `pip` yerine **`python -m pip`** kullan. Bazı antivirüs programları (ör. Avast) venv'in içindeki `pip.exe` dosyasını şüpheli sanıp engelliyor. `python -m pip` bu sorunu önler.

Kurulumu test et:

```powershell
python -c "import sentence_transformers, chromadb, ollama, streamlit, dotenv; print('Hepsi calisiyor!')"
```

İlk seferde 1-2 dakika sürebilir. Sonunda **"Hepsi calisiyor!"** yazmalı.

---

## Bölüm 6 — Yerel yapay zekâ modeli (Ollama)

**Ne:** Ollama, yapay zekâ modellerini **kendi bilgisayarında** çalıştıran ücretsiz bir program. Projede cevapları yazan model (LLM) bununla çalışıyor.

**Neden:** Proje dokümanı, yerel bir model ile sunucudaki (ücretli) bir modelin karşılaştırılmasını istiyor. Yerel taraf bu.

### 6.1 NVIDIA ekran kartı varsa: Sürücüyü güncelle

Model ekran kartında çalışırsa çok daha hızlı olur. Ekran kartını kontrol et:

```powershell
nvidia-smi
```

- **Bir tablo çıkarsa** NVIDIA kartın var. Tablodaki `Driver Version` değerine bak. Eskiyse (ör. 500'lü sayılar) https://www.nvidia.com/Download/index.aspx adresinden en yeni sürücüyü indirip kur (kurulumda **Express** seç).
- **Hata verirse** NVIDIA kartın yok. Sorun değil, model işlemcide çalışır, sadece daha yavaş olur.

### 6.2 Ollama'yı kur

```powershell
winget install Ollama.Ollama
```

Kurulumdan sonra bir karşılama penceresi açılır:
- **Continue**'ya tıkla.
- Hesap açmanı isterse **"No thanks, I'll use Ollama locally"** seç. Hesap sadece Ollama'nın bulut hizmeti için, bize gerekli değil.
- Son pencereyi kapatabilirsin. Ollama arka planda çalışmaya devam eder.

### 6.3 PowerShell'i tamamen kapatıp yeniden aç, sonra kontrol et

```powershell
ollama --version
```

### 6.4 Modeli indir (yaklaşık 2 GB)

```powershell
ollama pull llama3.2
```

Sonunda **"success"** yazmalı.

### 6.5 Test et

```powershell
ollama run llama3.2
```

`>>>` işareti çıkınca modele İngilizce bir soru yaz. Cevap verirse çalışıyor demektir. Çıkmak için `/bye` yaz.

---

## Bölüm 7 — Her çalışmaya başlarken

PowerShell'i her açtığında venv kapalı olur. Çalışmaya başlamadan önce şu üç komutu çalıştır:

```powershell
cd $HOME\Projects\CiteOrAbstain
```

```powershell
.\venv\Scripts\Activate.ps1
```

```powershell
git pull
```

- **İlk ikisi:** Proje klasörüne girer ve venv'i açar. Satırın başında `(venv)` olmalı. **`(venv)` yoksa kütüphane kurma ve kod çalıştırma.**
- **`git pull`:** Arkadaşlarının GitHub'a gönderdiği değişiklikleri bilgisayarına indirir. Kimse bir şey göndermediyse "Already up to date" der.

---

## Bölüm 8 — Dosyalarını GitHub'a göndermek

### Yol A: Tarayıcıdan yükleme (1. hafta için en kolayı)

Hiçbir şey kurmadan yapabilirsin:

1. https://github.com/dilarayaprak/CiteOrAbstain adresine git.
2. Dosyanın gideceği klasöre gir (ör. `docs`, `literature`, `evaluation`).
3. **Add file → Upload files**'a tıkla ve dosyayı sürükleyip bırak.
4. Alta kısa bir açıklama yaz (ör. "Add literature review table") ve **Commit changes**'a tıkla.

Bu şekilde yüklenen dosyalar da **senin adınla** görünür.

### Yol B: Bilgisayarından Git ile gönderme (2. haftadan itibaren)

Bir dosyayı oluşturduktan ya da değiştirdikten sonra üç adım var. Bunu bir **kargo** gibi düşün:

| Adım | Komut | Benzetme |
|---|---|---|
| 1. Seç | `git add dosya_adi` | Eşyayı valize koy |
| 2. Kaydet | `git commit -m "açıklama"` | Valizi kapat, üstüne etiket yapıştır |
| 3. Gönder | `git push` | Valizi kargoya ver |

**Sıra her zaman: add → commit → push.** En sık yapılan hata commit adımını atlamak. O zaman push "Everything up-to-date" der ve hiçbir şey gönderilmez.

Örnek:

```powershell
git status
```

Ne değiştiğini gösterir. Yeni dosyalar kırmızı renkte **Untracked** olarak görünür.

```powershell
git add docs/project_requirements.md
```

```powershell
git status
```

Dosya bu sefer **yeşil** görünmeli. Yani valize girdi.

```powershell
git commit -m "Add project requirements document"
```

```powershell
git push
```

Sonunda `main -> main` satırını görmelisin. GitHub sayfasını yenilersen dosyan orada olur.

**İyi bir commit mesajı** neyin yapıldığını kısa ve net söyler: "Add literature review table", "Fix typo in glossary" gibi. "update", "son hali" gibi mesajlardan kaçın. Hocamız bu geçmişi okuyabilir.

> ⚠️ **Bilmen gereken:** Bilgisayarındaki değişiklikler GitHub'a **kendiliğinden gitmez.** Sen push yapana kadar sadece senin bilgisayarında kalır. Arkadaşlarının değişiklikleri de sen `git pull` yapana kadar bilgisayarına gelmez.

---

## Bölüm 9 — Sık karşılaşılan sorunlar

| Sorun | Çözüm |
|---|---|
| **"running scripts is disabled"** (venv aktifleştirirken) | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| **"Authentication failed"** (clone veya push sırasında) | `git credential-manager github login` çalıştır, tarayıcıda izin ver, sonra tekrar dene. |
| **Yeni kurulan program "tanınmıyor"** (ör. `ollama`, `git`) | **Bütün** PowerShell pencerelerini kapatıp yeniden aç. |
| **Antivirüs (ör. Avast) pip'i engelliyor** | `pip` yerine `python -m pip` kullan. |
| **Push reddedildi, "pull first" diyor** | Biri senden önce bir şey göndermiş. `git pull`, sonra tekrar `git push`. |
| **Push "Everything up-to-date" dedi ama dosya gitmedi** | Commit adımını atlamışsın. `git add` → `git commit` → `git push` sırasını kontrol et. |
| **Komutlar birbirine yapıştı, garip hata** | Komutları tek tek kopyala. Hatalı satırı düzeltip tekrar çalıştır. |
| **Ekranda garip karakterler (ör. `GÃ¶ksu`)** | Sadece görüntüleme sorunu, dosya doğru. GitHub'da düzgün görünür. |
| **Kod çalışırken "module not found" hatası** | venv aktif değil. Satırın başında `(venv)` var mı kontrol et. Yoksa Bölüm 7'deki komutları çalıştır. |

Takıldığın yerde hata mesajının ekran görüntüsünü ekip grubuna at.

---

## Bölüm 10 — Deneyleri çalıştırmak (isteğe bağlı)

Dilara 1. haftada `notebooks/` klasörüne dört deney ekledi. Kodları, sonuçları ve Türkçe notları GitHub'da hiçbir şey kurmadan da görebilirsin. Kendi bilgisayarında çalıştırmak istersen:

**Jupyter notebook'ları:**

```powershell
python -m notebook
```

Tarayıcıda Jupyter açılır. `notebooks` klasörüne girip dosyaları aç. Bir hücreyi çalıştırmak için **Shift+Enter**.

> Yeni bir bilgisayarda **önce `02_chromadb_experiment.ipynb`**'yi çalıştır. Örnek pasajlar veritabanına bu notebook'ta ekleniyor. Veritabanı GitHub'a gönderilmediği için herkesin kendi bilgisayarında oluşturması gerekiyor.

Jupyter'ı kapatırken önce tarayıcı sekmelerini kapat, sonra PowerShell'de **Ctrl+C**'ye bas.

**Streamlit sohbet demosu:**

```powershell
python -m streamlit run notebooks/04_streamlit_demo.py
```

- İlk seferde e-posta sorarsa hiçbir şey yazmadan **Enter**'a bas.
- Tarayıcıda sohbet ekranı açılır. Ollama'nın çalışıyor olması gerekiyor.
- Kapatmak için PowerShell'de **Ctrl+C**.
