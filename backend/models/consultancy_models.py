from database.mysql_connector import db
from models.auth_models import Advisor, User
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field# Pydantic importları
from typing import ClassVar



"SQLALCHEMY MODELLERİ"

class ConsultantProfile(db.Model):
    """ Danışmanın kullanıcıyla buluşan bilgilerinin tutulduğu tablodur."""

    __tablename__ = 'consultant_profiles' #db de tablo adımız

    advisor_id = db.Column(db.Integer, db.ForeignKey('advisors.id'), primary_key=True) #databaseden advisor id bilgisini çek
    
    advisor = db.relationship(Advisor, backref=db.backref('profile', uselist=False)) #Advisor sql modeliyle ilişkiili olduğunu belirtelim.

    specialization = db.Column(db.String(255), nullable=True)
    bio_detailed = db.Column(db.String(512), nullable=True)#detaylı bilgi isteyen kullanıcıya gösterilir. danışmanın detaylı bilgi sayfasında
    profile_image_url = db.Column(db.String(512), nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def __repr__(self):
        return f'<ConsultantProfile AdvisorID={self.advisor_id}>'
    




class AvailabilitySlot(db.Model): 
    """Danışmanların ne zaman müsait olduğuna dair bilgileri tutar."""
    __tablename__ = 'availability_slots'

    slot_id = db.Column(db.Integer, primary_key=True) 
    advisor_id = db.Column(db.Integer, db.ForeignKey('advisors.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_booked = db.Column(db.Boolean, nullable=False, default=False)

    advisor = db.relationship(Advisor, backref=db.backref('availability_slots', lazy='dynamic'))

    def __repr__(self):
        return f'<AvailabilitySlot ID={self.slot_id}, AdvisorID={self.advisor_id}, Start={self.start_time}, End={self.end_time}, Booked={self.is_booked}>'





class Appointment(db.Model):
    """Randevu verilerini temsil eder. """

    __tablename__='appointments'


    appointment_id= db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    advisor_id= db.Column(db.Integer, db.ForeignKey('advisors.id'), nullable=False)
    start_time= db.Column(db.DateTime, nullable=False)
    end_time= db.Column(db.DateTime, nullable=False)
    status= db.Column(db.String(50), nullable=False, default='pending_confirmation')
    notes=db.Column(db.String(500), nullable=True)#kullanıcının not eklemesi opsiyoneldir. isterese eklemez.
    meeting_link= db.Column(db.String(500), nullable=True)#Danışman link paylaşmalı.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    #relationships
    user= db.relationship(User, backref='user_appointments')
    advisor=db.relationship(Advisor, backref='advisor_appointments')
    availability_slot = db.relationship('AvailabilitySlot', backref=db.backref('appointment', uselist=False))

    availability_slot_id = db.Column(db.Integer, db.ForeignKey('availability_slots.slot_id'), unique=True, nullable=True)
    def __repr__(self):
        return f'<Appointmen ID={self.appointment_id}, User ID= {self.user_id}, Advisor ID={self.advisor_id}, Status={self.status}'
    




class Feedback(db.Model):
    """Randevusu başarıyla tamamlanan kullanıcıların geri bildirimde bulunma senaryosunu içerir."""

    __tablename__='feedbacks'

    feedback_id = db.Column(db.Integer, primary_key=True)
    appntmnt_id= db.Column(db.Integer, db.ForeignKey('appointments.appointment_id'), nullable=False)
    user_id= db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    advisor_id= db.Column(db.Integer, db.ForeignKey('advisors.id'), nullable=False)
    rating=db.Column(db.Integer,nullable=False)#0 ile 5 arasında olmalı. frontendde tuşlama yapalım. 0 dan 5 e kadar seçenekler olsun.
    comment=db.Column(db.String(500), nullable=True)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

    appointment = db.relationship('Appointment', backref=db.backref('feedbacks', lazy='dynamic')) 
    user=db.relationship(User, backref=db.backref('user_feedbacks', lazy='dynamic'))
    advisor=db.relationship(Advisor, backref=db.backref('advisor_feedbacks', lazy='dynamic'))


    def __repr__(self):
        return f'<Feedback ID={self.feedback_id}, User ID= {self.user_id}, Advisor ID={self.advisor_id}, RATING={self.rating}> '







"""PYDANTIC MODELLERI"""


class OrmConfig(BaseModel): # Temel Yapılandırma olarak değiştirildi v2 ye uyumlu hale geldi
    """Pydantic modellerinin SQLAlchemy ile uyumlu çalışması için temel yapılandırma."""
    from_attributes: ClassVar[bool] = True

class ConsultantInfoBase(BaseModel):
    """Danışman listelemek için basemodel"""
    id: int = Field(description="Danışmanın sistemdeki ID'si (Advisor ID).", example=101)
    firstName: str = Field(description="Danışmanın adı.", example="Ayşe")
    lastName: str = Field(description="Danışmanın soyadı.", example="Danış")
    email: EmailStr = Field(description="Danışmanın e-posta adresi.", example="ayse.danis@example.com")

    model_config = {
        "from_attributes": True
    }

class ConsultantProfileResponse(ConsultantInfoBase):
    """Seçilen danışmanın detaylı bilgilerini döndürmek için"""
    specialization: Optional[str] = Field(None, description="Danışmanın uzmanlık alanı.", example="Bütçe Yönetimi")
    bio_detailed: Optional[str] = Field(None, description="Danışmanın detaylı biyografisi.", example="Kişisel finans ve bütçe yönetimi...")
    profile_image_url: Optional[str] = Field(None, description="Danışmanın profil fotoğrafının URL'si.", example="https://example.com/images/ayse.jpg")
    experience_years: Optional[int] = Field(None, description="Danışmanın deneyim yılı.", example=10)
    averageRating: Optional[float] = Field(None, ge=0, le=5, description="Danışmanın ortalama kullanıcı puanı (0-5).", example=4.5)

    model_config = {
        "from_attributes": True
    }



#appointment durum seçenekleri
AppointmentStatus = Literal["pending_confirmation", "confirmed", "completed"]
AdvisorAppointmentUpdateStatus = Literal["confirmed", "completed"]

# Appointment Modelleri
class AppointmentBase(BaseModel):
    """Randevular için temel sınıf"""

    start_time: datetime = Field(example="2025-05-15T10:00:00Z")
    end_time: datetime = Field( example="2025-05-15T10:50:00Z")
    notes: Optional[str] = Field(None, example="Bütçe planlama konusunda yardım almak istiyorum.")

class CreateAppointmentRequest(BaseModel):
    """Kullanıcının randevu oluşturma isteği için """

    consultantId: int = Field(description="Randevu alınmak istenen danışmanın ID'si (Advisor ID).", example=101)
    slotId: int = Field(description="Danışmanın takviminden seçilen uygun zaman aralığının ID'si (AvailabilitySlot slot_id).", example=1)
    notes: Optional[str] = Field(None, max_length=500, description="Kullanıcının danışmana iletmek istediği notlar (opsiyonel).")

class AppointmentResponse(AppointmentBase):
    """API'den dönecek detaylı randevu bilgisi için """

    appointment_id: int = Field(example=5001)
    user_id: int = Field(example=1)
    advisor_id: int = Field(example=101)
    status: AppointmentStatus = Field(example="confirmed")
    meeting_link: Optional[str] = Field(None, example="https://meet.example.com/session123")
    created_at: datetime
    updated_at: datetime
    
    userFirstName: Optional[str] = Field(None, example="Ali")
    userLastName: Optional[str] = Field(None, example="Veli")
    consultantFirstName: Optional[str] = Field(None, example="Ayşe")
    consultantLastName: Optional[str] = Field(None, example="Danış")
    availability_slot_id: Optional[int] = Field(None, example=1)

    model_config = {
        "from_attributes": True
    }
    
class UpdateAppointmentRequestAdvisor(BaseModel):
    """Danışmanın bir randevuyu güncelleme isteği için Pydantic modeli."""

    status: Optional[AdvisorAppointmentUpdateStatus] = Field(None, description="Danışman tarafından güncellenecek randevu durumu.")
    meeting_link: Optional[str] = Field(None, description="Online görüşme linki.")



# Feedback Modelleri



class RateAppointmentRequest(BaseModel): 
    """Kullanıcının bir randevuyu puanlama isteği için Pydantic modeli."""

    rating: int = Field(..., description="Verilen puan (1-5 arası).", example=5) 
    comment: Optional[str] = Field(None, max_length=500, description="Puanlama yorumu (opsiyonel).", example="Çok yardımcı oldu, teşekkürler.")

class FeedbackResponse(BaseModel): 
    """API'den dönecek geri bildirim detayı için Pydantic modeli."""

    feedback_id: int
    appntmnt_id: int 
    user_id: int
    advisor_id: int 
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    userFirstName: Optional[str] = Field(None, description="Geri bildirimi yapan kullanıcının adı.") # Servis katmanında doldurulacak

    model_config = {
        "from_attributes": True
    }



# AvailabilitySlot Modelleri
AvailabilitySlotStatus = Literal["available", "booked"]

class AvailabilitySlotResponse(BaseModel): 
    """API'den dönecek uygunluk zaman aralığı detayı için Pydantic modeli."""

    slot_id: int 
    start_time: datetime
    end_time: datetime
    status: AvailabilitySlotStatus 

    model_config = {
        "from_attributes": True
    }

class AvailabilitySlotCreate(BaseModel): 
    """Danışmanın takvimini güncellerken gönderilecek her bir slot için Pydantic modeli."""

    start_time: datetime
    end_time: datetime

class UpdateConsultantScheduleRequest(BaseModel): 
    """Danışmanın kendi uygunluk takvimini güncelleme isteği için Pydantic modeli."""

    timeZone: Optional[str] = Field(None, description="Takvimdeki zamanların ait olduğu zaman dilimi (örn: Europe/Istanbul).", example="Europe/Istanbul")
    availabilitySlots: List[AvailabilitySlotCreate] = Field(description="Danışmanın uygunluk zaman aralıkları listesi.")


