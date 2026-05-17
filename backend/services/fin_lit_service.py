from models.fin_lit_models import (
EducationApplication, 
ApplicationRequest,
HomePageInfo,
CourseContentPackage,
ApplicationForm)
from flask import current_app 
from sqlalchemy.exc import IntegrityError
from models.fin_lit_models import EducationApplication, Education
from database.mysql_connector import db
from datetime import datetime
from exceptions.auth_error_handler import (
    ApiBaseError,
    NotFoundError, 
    ConflictError, 
    EducationNotFoundError,
    ApplicationNotFoundError,
    DuplicateApplicationError,
    QuotaFullError,
    InvalidApplicationStatusError
)
from config.config import Keys




class FinancialLiteracyService:

    def create_education_application(self, application_data: dict) -> dict:
        """
        Yeni bir eğitim başvurusu oluşturur. Kontenjanı kontrol eder ve
        duruma göre başvuruyu 'onaylandı' olarak kaydeder veya kontenjan doluysa
        QuotaFullError fırlatır (başvuru oluşturulmaz).
        application_data: ApplicationRequest Pydantic modelinden .model_dump() ile gelen sözlük.
        """
        education_id_from_request = application_data.get("educationId")
        if education_id_from_request is None:
            raise ApiBaseError(message="Başvurulan eğitim ID'si (educationId) istek gövdesinde eksik.",
                               status_code=400, error_code="MISSING_EDUCATION_ID")
        
        education = db.session.get(Education, education_id_from_request)
        if not education:
            raise EducationNotFoundError(message=f"ID'si {education_id_from_request} olan eğitim bulunamadı.")
 
        approved_count = education.applications.filter_by(status='onaylandı').count() #onaylanan başvuru sayısını say

        if approved_count >= education.quota: # Kontenjan doluysa 
            raise QuotaFullError(message=f"'{education.name}' eğitimi için kontenjan dolu. Başvurunuz alınamadı.")
        
        application_status = 'onaylandı' 
        response_message = "Başvurunuz başarılı. Kontenjanda yer olduğu için başvurunuz onaylanmıştır."
        #kullanıcıya onay e postası  ileride gönderilebilir.

        try:
            new_application = EducationApplication(
                first_name=application_data.get("firstName"),
                last_name=application_data.get("lastName"),
                email=application_data.get("email"),
                phone=application_data.get("phone"),
                gender=application_data.get("gender"),
                age=application_data.get("age"),
                education_id=education.id,
                status=application_status 
            )
            
            db.session.add(new_application)
            db.session.commit()

            return {
                "mesaj": response_message,
                "basvuruId": str(new_application.id),
                "durum": new_application.status
            }
        except IntegrityError:
            db.session.rollback()
            raise DuplicateApplicationError() # Mesaj zaten hata sınıfında tanımlı
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"create_education_application sırasında beklenmedik hata: {str(e)}")
            raise ApiBaseError(message="Başvuru sırasında beklenmedik bir sunucu hatası oluştu.")
    

    def get_fin_lit_home_page_content(self) -> dict:
        """Finansal okuryazarlık ana sayfası için ilgili verileri döndürür."""
        return {
            "baslik": "Finansal Okuryazarlığa Hoş Geldiniz!",
            "aciklama": "Kişisel finanslarınızı yönetmeyi öğrenin, bütçenizi planlayın ve yatırım hedeflerinize ulaşın.",
            "bolumler": [
                {
                    "bolumBasligi": "Neden Finansal Okuryazarlık?",
                    "bolumIcerigi": "Finansal okuryazarlık, paranızı daha iyi anlamanıza, borçlarınızı yönetmenize ve geleceğiniz için daha güvenli kararlar almanıza yardımcı olur."
                },
                {
                    "bolumBasligi": "Platformumuzda Neler Var?",
                    "bolumIcerigi": "Eğitim modülleri, bütçe planlama araçları, kişiselleştirilmiş öneriler ve uzman danışmanlık hizmetleri."
                }
            ]
        }
    
    def get_course_package_details(self)->dict:
        """Kurs detaylarını getirir."""
        return {
            "paketAdi": "Temel Finansal Okuryazarlık Paketi",
            "paketAciklamasi": "Bu paket, bütçeleme, tasarruf, borç yönetimi ve temel yatırım konularını kapsamaktadır.",
            "moduller": [
                {
                    "haftaAdi": "Hafta 1: Bütçeleme Sanatı",
                    "aciklama": "Gelir ve giderlerinizi nasıl takip edeceğinizi, etkili bir bütçe oluşturmayı öğreneceksiniz."
                },
                {
                    "haftaAdi": "Hafta 2: Akıllı Tasarruf Yöntemleri",
                    "aciklama": "Kısa ve uzun vadeli hedefleriniz için nasıl tasarruf yapabileceğinizi keşfedin."
                },
                {
                    "haftaAdi": "Hafta 3: Yatırıma Giriş",
                    "aciklama": "Temel yatırım kavramları, risk yönetimi ve farklı yatırım araçları hakkında bilgi edinin."
                }
            ]
        }
    

    def get_application_form_data(self) -> dict:
        """
        Başvuru formu için (varsa) statik veriyi döndürür.
        (ApplicationForm Pydantic modeline uygun olmalı)
        """
        return {
            "formBasligi": "Finansal Okuryazarlık Eğitim Programı Başvuru Formu"
        }
    
