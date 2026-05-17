from datetime import datetime
from typing import List, Optional, Dict
from database.mysql_connector import db 
from models.auth_models import Advisor, User
from models.consultancy_models import ConsultantProfile, AvailabilitySlot, Appointment, Feedback
from exceptions.auth_error_handler import (
    ApiBaseError,
    NotFoundError, 
    ConflictError, 
)

from models.consultancy_models import (
    CreateAppointmentRequest,
    RateAppointmentRequest,
    UpdateAppointmentRequestAdvisor,
    UpdateConsultantScheduleRequest,
    AvailabilitySlotCreate 
)




class ConsultancyService:



    def list_consultants(self)->List[Advisor]:
        """GET/consultants ın service teki iş mantığı. """

        try:
            advisors=Advisor.query.all()#veritabanından danışman bilgilerini çek
            return advisors
        
        except Exception as e:
            raise Exception(f"Danışmanlar listelenirken bir sorun oluştu: {str(e)}")
    
    def get_consultant_profile_details(self, advisor_id:int)->Advisor:
        """ Seçilen danışmanın detaylı bilgilerini getirir."""

        try:
            advisor = Advisor.query.filter_by(id=advisor_id).first()
            
            if not advisor:
                raise NotFoundError(f"Danışman ID {advisor_id} bulunamadı.")

            return advisor
        except NotFoundError: 
            raise
        except Exception as e:
            raise Exception(f"Danışman detayı alınırken bir sorun oluştu: {str(e)}")
        
    def get_consultant_availability(self, advisor_id: int) -> List[AvailabilitySlot]:
        """Seçilen danışmanın uygun günlerini getirir."""
        try:
            advisor= Advisor.query.filter_by(id= advisor_id).first()#seçilen danışmanı veritanından çek
            if not advisor:
                raise NotFoundError(f"Danışman ID {advisor_id} bulunamadı, bu nedenle uygunluk durumu alınamıyor.")

            available_slots = AvailabilitySlot.query.filter_by(advisor_id=advisor_id, is_booked=False).order_by(AvailabilitySlot.start_time).all()
            return available_slots
        except NotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Danışmanın uygun günleri çekilirken bir hata oluştu: {str(e)}")





    def create_appointment(self, user_id: int, appointment_data: CreateAppointmentRequest) -> Appointment:
        """POST /appointments/request giriş yapmış bir kullanıcının randevusunu oluşturmak."""

        try:
            slot_id= appointment_data.slotId #pydantic modelinden slot idye eriş
            advisor_id=appointment_data.consultantId
            available_slot= AvailabilitySlot.query.filter_by(slot_id=slot_id).first()
            if not available_slot:
                raise NotFoundError("Seçilen zaman aralığı bulunamadı.")
            if available_slot.is_booked:
                raise ConflictError("Bu zaman aralığı dolu.")

            new_appointment = Appointment(
                    user_id=user_id,
                    advisor_id=advisor_id, 
                    start_time=available_slot.start_time,
                    end_time=available_slot.end_time,
                    notes=appointment_data.notes,
                    availability_slot_id=available_slot.slot_id, 
                    status='pending_confirmation' 
            ) #yeni randevuyu oluşturdum.
            #şimdi seçilen randevunun durumunu booked yapalım.
            available_slot.is_booked=True
            db.session.add(new_appointment)
            db.session.add(available_slot)
            db.session.commit()

            return new_appointment
        except NotFoundError:
                db.session.rollback()
                raise
        except ConflictError as e:
                db.session.rollback()
                raise ConflictError(str(e)) 
        except Exception as e:
                db.session.rollback()
                raise ApiBaseError(f"Randevu oluşturulurken bir hata oluştu: {str(e)}")


    
    def get_user_appointments(self, user_id: int, status_filter: Optional[str] = None) -> List[Appointment]:
        """Giriş yapan kullanıcnın randevularını listeler."""
        try:
            appointments=Appointment.query.filter_by(user_id=user_id)
            if status_filter:
                    appointments = appointments.filter_by(status=status_filter)
            filtered_appointments=appointments.all()
            return filtered_appointments
        except Exception as e:
                raise Exception(f"Randevularınız listelenirken bir sorun oluştu: {str(e)}")


    def get_user_appointment_details(self, user_id: int, appointment_id: int) -> Appointment:
        """Kullanıcının istediği randevu detayına ulaşabilmesini amaçlar."""
        try:
            selected_appointment=Appointment.query.filter_by(user_id=user_id, appointment_id=appointment_id).first()
            if not selected_appointment:
                raise NotFoundError("İlgili randevu detayları bulunmadı.")
            return selected_appointment
        except NotFoundError: # Kendi NotFoundError'ımızı mesajıyla birlikte tekrar fırlatıyoruz
                raise
        except Exception as e:
                raise Exception(f"Randevularınız listelenirken bir sorun oluştu: {str(e)}")

        
    def submit_appointment_rating(self, user_id: int, appointment_id: int, rating_data: RateAppointmentRequest) -> Feedback:
        """Kullanıcının tamamlanan randevusunu puanlaması."""

        try:
            
            current_appointment= Appointment.query.filter_by(user_id=user_id, appointment_id=appointment_id).first()

            if not current_appointment:
                    raise NotFoundError(f"Puanlanacak randevu bulunamadı ")
            
            if current_appointment.status != "completed":
                raise ConflictError("Sadece tamamlanmış randevular puanlanabilir.")

            
            feedback_status=Feedback.query.filter_by(appntmnt_id=appointment_id).first()
            if feedback_status:
                raise ConflictError(f"Randevular sadeec 1 kez değerlendirilebilir.")
            new_feedback=Feedback(
                appntmnt_id= appointment_id,
                user_id= user_id,
                advisor_id= current_appointment.advisor_id,
                rating=rating_data.rating,
                comment=rating_data.comment
            )
            db.session.add(new_feedback)
            db.session.commit()
            return new_feedback
        except NotFoundError as e:
                db.session.rollback()
                raise NotFoundError(str(e))
        except ConflictError as e: 
                db.session.rollback()
                raise ConflictError(str(e)) 
        except Exception as e:
                db.session.rollback()
                raise Exception(f"Oylama esnasında bir sorun oluştu: {str(e)}")
        
        
    def get_advisor_appointments(self, advisor_id: int, status_filter: Optional[str] = None) -> List[Appointment]:
        """Danışmana randevularını listeler. GET /advisor/me/appointments"""
        try:
            advisor_appointment_information = Appointment.query.filter_by(advisor_id=advisor_id)
            if status_filter:
                advisor_appointment_information=advisor_appointment_information.filter_by(status=status_filter)
            selected_all_appointments= advisor_appointment_information.all()
            return selected_all_appointments
        except Exception as e:
                raise Exception(f"Randevularınız listelenirken bir sorun oluştu: {str(e)}")
    
    def update_advisor_appointment(self, advisor_id: int, appointment_id: int, update_data: UpdateAppointmentRequestAdvisor) -> Appointment:
        """Danışman seçtiği randevunun durumunu günceller. (PATCH /advisor/me/appointments/{appointmentId})"""
        try:
            appointment_to_update = Appointment.query.filter_by(
                advisor_id=advisor_id,
                appointment_id=appointment_id
            ).first()
            
            if not appointment_to_update:
                raise NotFoundError(f"Güncellenecek randevu ID {appointment_id} bulunamadı veya bu danışmana ait değil.")

            # Sadece istekte gönderilen alanları güncelle (PATCH semantiği)
            updated_fields = update_data.model_dump(exclude_unset=True)

            if 'status' in updated_fields:
                appointment_to_update.status = updated_fields['status']
            
            if 'meeting_link' in updated_fields:
                appointment_to_update.meeting_link = updated_fields['meeting_link']
            
            db.session.commit()
            
            return appointment_to_update
            
        except NotFoundError as e:
            db.session.rollback()
            raise NotFoundError(str(e)) 
        except Exception as e:
                db.session.rollback()

                raise ApiBaseError(
                    message=f"Randevu güncelleme esnasında beklenmedik bir sorun oluştu.",
                    details={"original_exception": str(e)}, # Burayı düzeltin
                    status_code=500
                )

        
    def update_advisor_schedule(self, advisor_id: int, schedule_data: UpdateConsultantScheduleRequest) -> List[AvailabilitySlot]:
        """Danışmanın kendi takvimini güncellemesi. (PUT /advisor/me/schedule)"""
        try:
            AvailabilitySlot.query.filter_by(advisor_id=advisor_id, is_booked=False).delete(synchronize_session=False)  #boş olanları sil

            new_slots = [] #yeni slot listesi aç
            if schedule_data.availabilitySlots:
                for slot_data in schedule_data.availabilitySlots:
                    new_slot = AvailabilitySlot(
                        advisor_id=advisor_id,
                        start_time=slot_data.start_time,
                        end_time=slot_data.end_time,
                        is_booked=False # Yeni oluşturulan slotlar her zaman boştur
                    )
                    db.session.add(new_slot)
                    new_slots.append(new_slot)
            
            db.session.commit()
            return new_slots
            
        except Exception as e:
            db.session.rollback()
            raise ApiBaseError(f"Takvim güncelleme sırasında beklenmedik bir sorun oluştu: {str(e)}")
            
        
          



    def get_advisor_feedback(self, advisor_id: int) -> List[Feedback]:
        """Danışmanın kendine ait geri bildirimlere ulaşabilmesi"""
        try:
            filtered_advisor_feedbacks=Feedback.query.filter_by(advisor_id=advisor_id).all()
            if not filtered_advisor_feedbacks:
                 return filtered_advisor_feedbacks
            return filtered_advisor_feedbacks
            
        except Exception as e:
            raise ApiBaseError(f"Geri bildirimlere erişim esnasında beklenmedik bir sorun oluştu: {str(e)}")
             
