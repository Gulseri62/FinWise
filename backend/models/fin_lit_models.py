import re
from pydantic import BaseModel, EmailStr, Field, ConfigDict 
from datetime import datetime
from typing import List, Optional
from database.mysql_connector import db
from config.config import Keys

"""SQLAlchemy MODELLERİ"""

class Education(db.Model):
    """Eğitim paketinin genel bilgilerini içeren databasedir."""
    __tablename__ = 'educations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True, default="Finansal Okuryazarlık Eğitimi")
    description = db.Column(db.Text, nullable=True, default="Temel finansal okuryazarlık eğitimi.")
    quota = db.Column(db.Integer, nullable=False, default=0) 
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    applications = db.relationship('EducationApplication', backref='education', lazy='dynamic') 

    def __repr__(self):
        return f"<Education {self.id} - {self.name} (Kontenjan: {self.quota})>"

class EducationApplication(db.Model):
    """Eğitime başvuru yapan adayların bilgilerini içeren databasedir."""
    __tablename__ = 'education_applications'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    age = db.Column(db.Integer, nullable=False)
    application_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    education_id = db.Column(db.Integer, db.ForeignKey('educations.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='beklemede')

    def __repr__(self):
        return f"<EducationApplication {self.id} - {self.email} for Education ID {self.education_id}>" 

"""PYDANTIC MODELLERİ"""

class FinLitBaseModel(BaseModel):
    """Tüm finansal okuryazarlık Pydantic sınıfları için temel sınıf"""
    model_config = ConfigDict(
        extra='forbid',  #ekstra bir şeyle karşılaaşırsa 
    )

class ApplicationRequest(FinLitBaseModel):
    firstName: str = Field(min_length=2, description="Başvuru yapan kişinin adı.")
    lastName: str = Field(min_length=2, description="Başvuru yapan kişinin soyadı.")
    email: EmailStr = Field(description="Başvuran kişinin e-posta adresi.")
    phone: Optional[str] = Field(default=None, description="Başvuran kişinin telefon numarası (opsiyonel)") #default= none çünkü bu kısım opsiyonel
    gender: Optional[str] = Field(default=None, description="Başvuran kişinin cinsiyeti (opsiyonel)") 
    age: int = Field(gt=0, description="Başvuran kişinin yaşı (0'dan büyük olmalı).")
    educationId: int = Field(description="Başvurulan eğitimin ID'si.") 

    
    model_config = ConfigDict( 
        json_schema_extra={
            "example": {
                "firstName": "Ayşe",
                "lastName": "Kaya",
                "email": "aysekaya@example.com",
                "phone": "5551234567",
                "gender": "female",
                "age": 25,
                "educationId": 1
            }
        }
    )

class ApplicationResponse(FinLitBaseModel):
    mesaj: str = Field(description="Başvuru işlemi sonucu mesaj")
    basvuruId: Optional[str] = Field(default=None, description="Başarılı başvuruya atanan ID") 
    durum: Optional[str] = Field(default=None, description="Başvurunun güncel durumu") 

class Section(FinLitBaseModel):
    bolumBasligi: str
    bolumIcerigi: str

class HomePageInfo(FinLitBaseModel):
    baslik: str = Field(description="Sayfanın ana başlığı.")
    aciklama: str = Field(description="Sayfa hakkında genel açıklama.")
    bolumler: List[Section] = Field(description="Ana sayfa bölümleri.")

class Items(FinLitBaseModel): 
    haftaAdi: str
    aciklama: str

class CourseContentPackage(FinLitBaseModel):
    paketAdi: str = Field(description="Eğitim paketinin adı.") 
    paketAciklamasi: Optional[str] = Field(default=None, description="Eğitim paketinin genel açıklaması.") 
    moduller: List[Items] = Field(description="Eğitim paketinin modülleri.")

class ApplicationForm(FinLitBaseModel):
    formBasligi: str = Field(description="Form içeriğinin tamamı. Frontendin dizaynına bırakılmıştır.")

class EducationBase(FinLitBaseModel):
    name: str
    description: Optional[str] = None
    quota: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class EducationCreateRequest(EducationBase):
    pass

class EducationUpdateRequest(EducationBase):
    name: Optional[str] = None
    description: Optional[str] = None
    quota: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class EducationResponse(EducationBase):
    id: int
    approved_application_count: Optional[int] = Field(default=0, description="Bu eğitime onaylanmış başvuru sayısı")
    model_config = ConfigDict(from_attributes=True) # SQLAlchemy modelinden Pydantic modeline dönüşüm için


