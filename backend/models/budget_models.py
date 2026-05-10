from database.mysql_connector import db
from datetime import datetime, date 
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, EmailStr 
from typing import List, Optional, Literal 







""" SQLAlchemy Modeli """
class BudgetEntry(db.Model):
    __tablename__ = 'budget_entries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True) 
    entry_type = db.Column(db.Enum('income', 'expense', name='entry_type_enum'), nullable=False) # gelir veya gider
    amount = db.Column(db.Numeric(10, 2), nullable=False) 
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    entry_date = db.Column(db.Date, nullable=False, default=date.today) # İşlem tarihi
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    def __repr__(self):
        return f"<BudgetEntry id={self.id} user_id={self.user_id} type='{self.entry_type}' amount={self.amount} date='{self.entry_date}'>"
    



"""PYDANTIC MODELLERI"""



class BudgetEntryCreateRequest(BaseModel): # components.schemas.BudgetEntryCreateRequest 
    amount: float = Field(gt=0, description="İşlem tutarı (pozitif olmalı).")
    category: str = Field(min_length=1, max_length=100, description="İşlem kategorisi.")
    description: Optional[str] = Field(None, max_length=500, description="İşlem için opsiyonel açıklama.")
    entry_date: date = Field(description="İşlemin tarihi (YYYY-MM-DD).")

class BudgetEntryResponse(BaseModel): # components.schemas.BudgetEntryResponse 
    id: int = Field(description="Kaydın benzersiz ID'si.")
    user_id: int = Field(description="Kaydın ait olduğu kullanıcı ID'si.") # SQLAlchemy modelinden gelecek
    entry_type: Literal['income', 'expense'] = Field(description="İşlem tipi.")
    amount: float = Field()
    category: str = Field()
    description: Optional[str] = Field(None)
    entry_date: date = Field()
    created_at: datetime = Field()
    updated_at: datetime = Field()

    model_config = {
        "from_attributes": True
    }

class PaginatedBudgetEntryResponse(BaseModel): # components.schemas.PaginatedBudgetEntryResponse ile uyumlu
    total_items: int = Field(description="Filtrelerle eşleşen toplam kayıt sayısı.")
    total_pages: int = Field( description="Toplam sayfa sayısı.")
    current_page: int = Field( description="Mevcut sayfa numarası.")
    items_per_page: int = Field (description="Bu sayfadaki kayıt sayısı.") # API'de 'items_per_page', Pydantic'te 'per_page' olabilir, tutarlı olalım.
                                                                                  # API'deki 'items_per_page'e uygun şekilde bıraktım.
    items: List[BudgetEntryResponse] = Field(description="Bütçe kayıtları listesi.")


class BudgetReportResponse(BaseModel): # components.schemas.BudgetReportResponse ile uyumlu
    report_type_requested: Literal['daily', 'weekly', 'monthly'] = Field(description="İstek yapılan rapor tipi.")
    period_start_date: date = Field( description="Raporun kapsadığı dönemin başlangıç tarihi.")
    period_end_date: date = Field(description="Raporun kapsadığı dönemin bitiş tarihi.")
    total_income: float = Field()
    total_expense: float = Field()
    balance: float = Field()
    summary_by_category: Optional[List[dict]] = Field(None, example=[{"category": "Faturalar", "total_amount": 850.00, "entry_type": "expense"}])



class TransactionQuerySchema(BaseModel):
    start_date: Optional[date] = Field(None, description="Filtreleme için başlangıç tarihi (YYYY-MM-DD).")
    end_date: Optional[date] = Field(None, description="Filtreleme için bitiş tarihi (YYYY-MM-DD).")
    category: Optional[str] = Field(None, description="Filtreleme için kategori adı.")
    entry_type: Optional[Literal['income', 'expense']] = Field(None, description="Filtreleme için işlem tipi ('income' veya 'expense').")
    page: int = Field(1, gt=0, description="Sayfa numarası.")
    per_page: int = Field(10, gt=0, le=100, description="Sayfa başına kayıt sayısı.")

class BudgetReportRequestSchema(BaseModel):
    report_type: Literal['daily', 'weekly', 'monthly'] = Field(default='monthly', description="Rapor periyodu.")
