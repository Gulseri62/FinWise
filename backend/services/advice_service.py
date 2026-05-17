from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database.mysql_connector import db
from models.advice_models import (
    FinancialAdvice,
    AdviceFeedback,
    AdviceFeedbackRequest, 
    AdviceFeedbackResponse
)
from datetime import datetime, date, timedelta
from typing import List
from exceptions.auth_error_handler import ApiBaseError, NotFoundError, ConflictError
from sqlalchemy import desc, func 
from models.budget_models import BudgetEntry

class AdviceService:
    """
    Finansal Öneri Sistemi'nin servis katmanı sınıfı.
    """

    def record_feedback(self, user_id: int, feedback_data: AdviceFeedbackRequest) -> AdviceFeedback:
        """Geri bildirimi kaydeder. """
        try:
            # Geri bildirim yapılacak önerinin (FinancialAdvice) var olup olmadığını kontrol et.
            advice_exists = FinancialAdvice.query.get(feedback_data.advice_id)
            if not advice_exists:
                raise NotFoundError(message=f"ID'si {feedback_data.advice_id} olan finansal öneri bulunamadı.")

            existing_feedback = AdviceFeedback.query.filter_by(user_id=user_id,advice_id=feedback_data.advice_id).first()
            if existing_feedback:
                raise ConflictError(message="Bu öneriye daha önce geri bildirimde bulundunuz.")

            new_feedback = AdviceFeedback(
                advice_id=feedback_data.advice_id,
                user_id=user_id,
                is_helpful=feedback_data.is_helpful,
                comment=feedback_data.comment
            )

            db.session.add(new_feedback)
            db.session.commit()

            return new_feedback 

        except IntegrityError as e:
            db.session.rollback()
            raise ConflictError(
                message="Bu öneri için zaten bir geri bildirim mevcut veya başka bir veri bütünlüğü sorunu var.",
                details=str(e.orig)
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ApiBaseError(
                message="Geri bildirim kaydedilirken bir veritabanı hatası oluştu.",
                status_code=500,
                error_code="DATABASE_ERROR",
                details=str(e)
            )
        except Exception as e: 
            db.session.rollback()
            raise ApiBaseError(
                message="Geri bildirim kaydedilirken beklenmedik bir sunucu hatası oluştu.",
                details=str(e)
            )
    

    def get_personalized_advice(self, user_id: int) -> List[FinancialAdvice]:
        """Belirli bir kullanıcı için aktif olan finansal önerileri getirir."""
        try:
            
            advices = FinancialAdvice.query.filter_by(user_id=user_id,is_active=True # Sadece aktif önerileri getir
            ).order_by(
                desc(FinancialAdvice.priority), # Önce önceliğe göre 
                desc(FinancialAdvice.generated_at) # en son oluşturulan en üstte
            ).all()

            return advices

        except SQLAlchemyError as e:

            raise ApiBaseError(
                message="Finansal öneriler getirilirken bir veritabanı hatası oluştu.",
                status_code=500,
                error_code="DATABASE_ERROR",
                details=str(e)
            )
        except Exception as e:
            raise ApiBaseError(
                message="Finansal öneriler getirilirken beklenmedik bir sunucu hatası oluştu.",
                details=str(e)
            )


    def generate_personalized_advice(self, user_id: int) -> List[FinancialAdvice]:
        """
        Kullanıcının finansal verilerine göre basit, kural tabanlı kişiselleştirilmiş öneriler üretir
        ve bunları veritabanına kaydeder."""
        newly_generated_advices: List[FinancialAdvice] = []
        today = date.today()
        advice_period=30
        period_start_date = today - timedelta(days=advice_period)#öneri periyotunu 30 gün belirledim.
        period_end_date = today

        try:
            # 1. Kullanıcının son 30 günlük bütçe hareketlerini çek
            transactions = BudgetEntry.query.filter(
                BudgetEntry.user_id == user_id,
                BudgetEntry.entry_date >= period_start_date,
                BudgetEntry.entry_date <= period_end_date
            ).all()

            if not transactions:
                return newly_generated_advices

            total_income = sum(t.amount for t in transactions if t.entry_type == 'income') or 0.0
            total_expense = sum(t.amount for t in transactions if t.entry_type == 'expense') or 0.0
            
            # Kategori bazlı harcamalar
            expenses_by_category = {}
            for t in transactions:
                if t.entry_type == 'expense':
                    expenses_by_category[t.category] = expenses_by_category.get(t.category, 0.0) + float(t.amount)

            # 3. Kuralları Uygula ve Önerileri Oluştur
            generated_advice_details = [] 

            # Kural 1: Yüksek Harcama Oranı
            if total_income > 0 and (float(total_expense) / float(total_income)) > 0.80: # Gelirin %80'inden fazla harcama
                generated_advice_details.append((
                    f"Son 30 gündeki harcamalarınız ({total_expense:.2f} TL), gelirinizin ({total_income:.2f} TL) önemli bir kısmını oluşturuyor. Harcamalarınızı gözden geçirmeyi düşünebilirsiniz.",
                    "harcama_orani_yuksek",
                    4 # Yüksek öncelik
                ))

            # Kural 2: Belirli Bir Kategoride Yüksek Harcama
            if total_expense > 0:
                for category, amount in expenses_by_category.items():
                    if (amount / float(total_expense)) > 0.30: # Toplam harcamanın %30'undan fazlası tek bir kategoride
                        generated_advice_details.append((
                            f"'{category}' kategorisindeki harcamalarınız ({amount:.2f} TL) son 30 gündeki toplam harcamalarınızın önemli bir payına sahip. Bu alanda tasarruf imkanlarını değerlendirebilirsiniz.",
                            "kategori_harcamasi_yuksek",
                            3 # Orta öncelik
                        ))
                        break # Şimdilik ilk bulunan yüksek harcamalı kategori için öneri verelim

            # Kural 3: Düşük Gelir Kaydı (Örnek)
            if total_income <= 100.0 and len(transactions) > 0 : # Örneğin 100 TL'den az ve en az bir işlem varsa
                 generated_advice_details.append((
                    f"Son {advice_period} günlük periyotta kayıtlı geliriniz çok düşük ({total_income:.2f} TL) veya hiç yok. Gelirlerinizi düzenli olarak kaydetmeyi unutmayın.",
                    "dusuk_gelir_kaydi",
                    2
                ))
            
            # 4. Oluşturulan Önerileri Kaydet (Eğer benzer aktif öneri yoksa)
            for text, type_val, priority_val in generated_advice_details:
                # Kullanıcı için bu tipte aktif bir öneri var mı diye kontrol et
                existing_active_advice = FinancialAdvice.query.filter(
                    FinancialAdvice.user_id == user_id,
                    FinancialAdvice.advice_type == type_val,
                    FinancialAdvice.is_active == True
                ).first()

                if not existing_active_advice:
                    new_advice = FinancialAdvice(
                        user_id=user_id,
                        advice_text=text,
                        advice_type=type_val,
                        priority=priority_val,
                        is_active=True
                    )
                    db.session.add(new_advice)
                    newly_generated_advices.append(new_advice)
            
            if newly_generated_advices: # Eğer yeni öneri eklendiyse commit et
                db.session.commit()

            return newly_generated_advices

        except SQLAlchemyError as e:
            db.session.rollback()

            raise ApiBaseError(
                message="Finansal öneriler üretilirken bir veritabanı hatası oluştu.",
                status_code=500,
                error_code="DATABASE_ERROR",
                details=str(e)
            )
        except Exception as e:
            db.session.rollback()
            raise ApiBaseError(
                message="Finansal öneriler üretilirken beklenmedik bir sunucu hatası oluştu.",
                details=str(e)
            )    
    


