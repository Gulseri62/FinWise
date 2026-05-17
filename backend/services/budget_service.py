from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database.mysql_connector import db
from models.budget_models import BudgetEntry, BudgetEntryCreateRequest,TransactionQuerySchema,PaginatedBudgetEntryResponse,BudgetEntryResponse,BudgetReportRequestSchema,BudgetReportResponse
from typing import Literal
from exceptions.auth_error_handler import (
    ApiBaseError,
    NotFoundError, 
    ConflictError, 
    AuthorizationError,
    EducationNotFoundError,
    ApplicationNotFoundError,
    DuplicateApplicationError,
    QuotaFullError,
    InvalidApplicationStatusError
)
from sqlalchemy import desc, func

from datetime import datetime, timedelta,date, time
import calendar




class BudgetService:
    """
    Bütçe Planlama Modülünün service katmanının ana sınıfı. 
    Bütün mantıksal bütçe işlemleri burada kodlanır.
    """

    def add_budget_entry(self, user_id:int,entry_data: BudgetEntryCreateRequest, entry_type: Literal['income', 'expense']) -> BudgetEntry:
        """Gelir veya gider girişi ekler."""
        try:
            new_entry = BudgetEntry(
                user_id=user_id,
                entry_type=entry_type, #user_id ve entry_type fonksiyon çağrısından gelir
                amount=entry_data.amount, # Pydantic modelinden gelen doğrulanmış veriden gelir
                category=entry_data.category,
                description=entry_data.description,
                entry_date=entry_data.entry_date
            )
            db.session.add(new_entry)
            db.session.commit()
            return new_entry
        
        except IntegrityError as e: 
            db.session.rollback()
            raise ConflictError(message="Bütçe kaydı oluşturulurken bir veri bütünlüğü sorunu oluştu. Lütfen girdiğiniz verileri kontrol edin.",)
        except SQLAlchemyError as e: # Diğer tüm SQLAlchemy hatalarını yakala
            db.session.rollback()
            raise ApiBaseError( 
                message="Bütçe kaydı oluşturulurken beklenmedik bir veritabanı hatası oluştu.",
                status_code=500,
                error_code="DATABASE_ERROR", 
                details=str(e)
            )
        except Exception as e: 
            db.session.rollback() 
            raise ApiBaseError( 
                message="Bütçe kaydı oluşturulurken beklenmedik bir sunucu hatası oluştu.",details=str(e))
    
    def get_transactions(self, user_id, query_params=TransactionQuerySchema)-> PaginatedBudgetEntryResponse:
        """İşlem geçmişini listeler. """
        try:
            query = BudgetEntry.query.filter_by(user_id=user_id)

            if query_params.start_date:
                query = query.filter(BudgetEntry.entry_date >= query_params.start_date)
            if query_params.end_date:
                query = query.filter(BudgetEntry.entry_date <= query_params.end_date)
            if query_params.category:
                query = query.filter(BudgetEntry.category.ilike(f"%{query_params.category}%")) #büyük küçük harf duyarsız arama
            if query_params.entry_type:
                query = query.filter(BudgetEntry.entry_type == query_params.entry_type)

            query = query.order_by(desc(BudgetEntry.entry_date), desc(BudgetEntry.created_at)) #en yeni kayıt en üstte listelenir


            pagination_result = query.paginate(
                page=query_params.page,
                per_page=query_params.per_page,
                error_out=False 
            )
            items_response = [BudgetEntryResponse.model_validate(item) for item in pagination_result.items]

            return PaginatedBudgetEntryResponse(
                total_items=pagination_result.total,
                total_pages=pagination_result.pages,
                current_page=pagination_result.page,
                items_per_page=pagination_result.per_page, 
                items=items_response
            )

        except SQLAlchemyError as e:
            db.session.rollback()
            raise ApiBaseError(
                message="İşlemler listelenirken bir veritabanı hatası oluştu.",
                status_code=500,
                error_code="DATABASE_ERROR",
                details=str(e)
            )
        except Exception as e: 
            db.session.rollback()
            raise ApiBaseError(message="İşlemler listelenirken beklenmedik bir sunucu hatası oluştu.",details=str(e))
    

    def delete_budget_entry(self, user_id: int, entry_id: int):
        """Bütçe girdilerini silebilme özelliği. DELETE /budget/transactions/{transactionId} """

        try:
            find_delete_entry= BudgetEntry.query.filter_by(id=entry_id).first()
            if not find_delete_entry:
                raise NotFoundError(message=f"ID'si {entry_id} olan bütçe kaydı bulunamadı.")
            if find_delete_entry.user_id != user_id:
                raise AuthorizationError(message="Bu kaydı silme yetkiniz bulunmamaktadır.") #403 için
            db.session.delete(find_delete_entry)#seçilen entryi sil
            db.session.commit()#veritabanına ulaştır
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ApiBaseError(
                message="Girdi silinirken bir veritabanı hatası oluştu.",
                status_code=500,
                error_code="DATABASE_ERROR",
                details=str(e)
            )
        except Exception as e: 
            db.session.rollback()
            raise ApiBaseError(message="Girdi silinirken beklenmedik bir sunucu hatası oluştu.",details=str(e))
    

    def generate_financial_report(self, user_id: int, report_params: BudgetReportRequestSchema)->BudgetReportResponse:
        """Finansal rapor üretir. GET /budget/report"""

        today = date.today()
        start_date: date
        end_date: date
        report_type = report_params.report_type

        if report_type == "daily":
            start_date = today
            end_date = today

        elif report_type == "weekly":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

        elif report_type == "monthly":
            start_date = today.replace(day=1)
            last_day_of_month = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day_of_month)

        else:
            raise ApiBaseError(
                message="Geçersiz rapor tipi.",
                status_code=400,
                error_code="INVALID_REPORT_TYPE"
            )

        try:
            # Toplam Gelir
            total_income = db.session.query(func.sum(BudgetEntry.amount)).filter(
                BudgetEntry.user_id == user_id,
                BudgetEntry.entry_type == 'income',
                BudgetEntry.entry_date >= start_date,
                BudgetEntry.entry_date <= end_date
            ).scalar() or 0.0

            # Toplam Gider
            total_expense = db.session.query(func.sum(BudgetEntry.amount)).filter(
                BudgetEntry.user_id == user_id,
                BudgetEntry.entry_type == 'expense',
                BudgetEntry.entry_date >= start_date,
                BudgetEntry.entry_date <= end_date
            ).scalar() or 0.0

            balance = float(total_income) - float(total_expense)

            # Kategoriye göre özet
            summary = db.session.query(
                BudgetEntry.category,
                BudgetEntry.entry_type,
                func.sum(BudgetEntry.amount).label('total_amount')
            ).filter(
                BudgetEntry.user_id == user_id,
                BudgetEntry.entry_date >= start_date,
                BudgetEntry.entry_date <= end_date
            ).group_by(
                BudgetEntry.category,
                BudgetEntry.entry_type
            ).order_by(
                BudgetEntry.entry_type,
                desc('total_amount')
            ).all()

            summary_by_category_list = []
            for category_summary in summary:
                summary_by_category_list.append({
                    "category": category_summary.category,
                    "total_amount": float(category_summary.total_amount),
                    "entry_type": category_summary.entry_type
                })

            return BudgetReportResponse(
                report_type_requested=report_type,
                period_start_date=start_date,
                period_end_date=end_date,
                total_income=float(total_income),
                total_expense=float(total_expense),
                balance=balance,
                summary_by_category=summary_by_category_list if summary_by_category_list else None
            )

        except SQLAlchemyError as e:
            raise ApiBaseError(
                message="Bütçe raporu oluşturulurken bir veritabanı hatası oluştu.",
                status_code=500,
                error_code="DATABASE_ERROR",
                details=str(e)
            )
        except Exception as e:
            raise ApiBaseError(
                message="Bütçe raporu oluşturulurken beklenmedik bir sunucu hatası oluştu.",
                details=str(e)
            )