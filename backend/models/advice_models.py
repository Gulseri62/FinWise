from database.mysql_connector import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum # Enum ve Boolean eklendi
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional

""" SQLAlchemy Modelleri """

class FinancialAdvice(db.Model):
    __tablename__ = 'financial_advice'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True) 
    advice_text = Column(Text, nullable=False)
    advice_type = Column(String(100), nullable=True, index=True) 
    priority = Column(Integer, nullable=True) 
    generated_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False) # Öneri hala geçerli mi?

    feedbacks = relationship("AdviceFeedback", back_populates="advice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FinancialAdvice id={self.id} user_id={self.user_id} type='{self.advice_type}'>"

class AdviceFeedback(db.Model):
    __tablename__ = 'advice_feedback'

    id = Column(Integer, primary_key=True, autoincrement=True,unique=True)
    advice_id = Column(Integer, ForeignKey('financial_advice.id'), nullable=False, index=True,unique=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True) # Geri bildirimi yapan kullanıcı
    is_helpful = Column(Boolean, nullable=False) 
    comment = Column(Text, nullable=True)
    feedback_at = Column(DateTime, default=datetime.utcnow)
    advice = relationship("FinancialAdvice", back_populates="feedbacks")

    def __repr__(self):
        return f"<AdviceFeedback id={self.id} advice_id={self.advice_id} user_id={self.user_id} helpful={self.is_helpful}>"


"""Pydantic Modelleri"""

class PersonalizedAdviceResponse(BaseModel): 
    advice_id: int = Field(description="Önerinin benzersiz ID'si.")
    advice_text: str = Field(description="Öneri metni.")
    advice_type: Optional[str] = Field(None, description="Önerinin kategorisi veya tipi.")
    generated_at: datetime = Field(description="Önerinin oluşturulma zamanı.")
    priority: Optional[int] = Field(None, description="Önerinin önceliği (1-Düşük, 5-Yüksek).")
    model_config = {
        "from_attributes": True
    }

class AdviceFeedbackRequest(BaseModel): 
    advice_id: int = Field(description="Geri bildirim yapılan önerinin ID'si.")
    is_helpful: bool = Field(description="Önerinin faydalı olup olmadığı.")
    comment: Optional[str] = Field(None, max_length=1000, description="Kullanıcının ek yorumları (opsiyonel).")

class AdviceFeedbackResponse(BaseModel): 
    feedback_id: int = Field(description="Geri bildirimin benzersiz ID'si.")
    advice_id: int = Field(description="Geri bildirim yapılan önerinin ID'si.")
    user_id: int = Field(description="Geri bildirimi yapan kullanıcının ID'si.")
    is_helpful: bool = Field()
    comment: Optional[str] = Field(None)
    feedback_at: datetime = Field(description="Geri bildirimin yapılma zamanı.")

    model_config = {
        "from_attributes": True
    }

