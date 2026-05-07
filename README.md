# FinWise


**Team members:**
Gülşeri DEMİR- Team LeaderFrontend
434345-Bilge Işık - Code Reviewer-Backend
434347-Sena TALİPOĞLU – Code Reviewer-Backend 



**Açıklama**
Pojemiz tasarlanırken backend ve frontend olmak üzere ikiye ayrılmıştır. PROJENİN SON HALİ MAIN BRANCH'ındadır. Proje %90 oranında tamamlanmıştır. Backend kodlarına bakmadan önce Backend klasörünün read me dosyasını okumalısınız.

**Kısa Tanım:**  

FinWise, bireylerin finansal okuryazarlığını artırmak, kişiselleştirilmiş danışmanlık hizmeti sunmak, bütçe yönetimini kolaylaştırmak ve akıllı finansal öneriler üretmek amacıyla geliştirilmiş modüler bir web uygulamasıdır.

---

## Özellikler

- **Kullanıcı Yönetimi (Auth)**  
  - Kayıt & Giriş (JWT tabanlı)  
  - Şifre sıfırlama & token yenileme  
  - Profil görüntüleme

- **Danışmanlık Modülü**  
  - Danışman listesi ve detaylı profilleri  
  - Danışman takvim yönetimi (slot ekleme/güncelleme)  
  - Randevu talebi, onay, tamamlama ve puanlama

- **Finansal Okuryazarlık**  
  - İnteraktif eğitim modülleri  
  - Kurs paketleri görüntüleme  
  - Eğitim başvurusu formu & onayı

- **Bütçe Planlayıcı**  
  - Gelir-gider takibi  
  - Kategori bazlı raporlama  
  - Günlük/aylık özetler

- **Finansal Öneri Sistemi**  
  - Kullanıcı davranışına göre kişiselleştirilmiş öneriler  
  - Öneri geri bildirim formu

---

## Teknik Yapı

- **Dil & Framework:** Python, Flask  
- **Veritabanı:** MySQL (mysql-connector-python)  
- **Veri Modelleri:** SQLAlchemy & Pydantic  
- **Kimlik Doğrulama:** PyJWT  
- **Yapılandırma:** python-dotenv  
- **CORS:** Flask-Cors  
- **Test:** pytest, schemathesis (OpenAPI testleri)  


## Kodu çalıştırmak için:

1-Yerelinize kodu çekin ve app.py'ı çalıştırın.
2-index.html dosyasını open with live server ile web sitesini açın.
