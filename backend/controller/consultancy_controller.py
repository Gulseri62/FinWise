from flask import request, jsonify
from pydantic import ValidationError as PydanticValidationError 
from service.consultancy_service import ConsultancyService
from service.auth_service import AuthService 
from config.config import Keys

from models.consultancy_models import (
    ConsultantInfoBase,
    ConsultantProfileResponse,
    AvailabilitySlotResponse,
    AvailabilitySlotStatus,
    CreateAppointmentRequest,
    AppointmentResponse,
    UpdateAppointmentRequestAdvisor,
    RateAppointmentRequest,
    FeedbackResponse,
    UpdateConsultantScheduleRequest
)

from exceptions.auth_error_handler import (
    ApiBaseError,
    NotFoundError, 
    ConflictError,
    AuthorizationError, 
    TokenError, 
    ValidationError  
)
import jwt 


consultancy_service = ConsultancyService()
auth_service = AuthService() 


def _get_current_user_info_from_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise AuthorizationError(message="Yetkilendirme başlığı eksik veya geçersiz.")
    
    token = auth_header.split(" ")[1]
    
    try:
        
        decoded_payload = jwt.decode(token, Keys.pem_public(), algorithms=["RS256"], # DÜZELTİLMİŞ SATIR
                               options={"require": ["exp", "sub", "email", "user_type"]})
        
        user_id = int(decoded_payload.get("sub"))
        user_type = decoded_payload.get("user_type")

        if not user_id or not user_type:
            raise TokenError(message="Token içeriği kullanıcı kimliği veya tipi için eksik.")
            
        return {"user_id": user_id, "user_type": user_type}

    except jwt.ExpiredSignatureError:
        raise TokenError(message="Token süresi dolmuş.")
    except jwt.InvalidTokenError:
        raise TokenError(message="Geçersiz token.")
    except TokenError:
        raise
    except Exception as e:

        raise AuthorizationError(message="Token doğrulama sırasında bir sorun oluştu.")



def list_consultants_controller():
    """GET /consultants - Tüm uygun danışmanları listeler."""
    advisors_sql = consultancy_service.list_consultants()
    response_data = [ConsultantInfoBase.model_validate(adv).model_dump() for adv in advisors_sql]
    return jsonify(response_data), 200

def get_consultant_profile_controller(consultant_id: int):
    """GET /consultants/{consultantId} - Belirli bir danışmanın detaylı profilini getirir."""
    advisor_sql = consultancy_service.get_consultant_profile_details(advisor_id=consultant_id)
    profile_info = advisor_sql.profile 
    average_rating = None 

    response_model_data = {
        "id": advisor_sql.id,
        "firstName": advisor_sql.firstName,
        "lastName": advisor_sql.lastName,
        "email": advisor_sql.email,
        "specialization": profile_info.specialization if profile_info else None,
        "bio_detailed": profile_info.bio_detailed if profile_info else None,
        "profile_image_url": profile_info.profile_image_url if profile_info else None,
        "experience_years": profile_info.experience_years if profile_info else None,
        "averageRating": average_rating,
        "created_at": profile_info.created_at if profile_info and hasattr(profile_info, 'created_at') else None,
        "updated_at": profile_info.updated_at if profile_info and hasattr(profile_info, 'updated_at') else None
    }
    response_data = ConsultantProfileResponse(**response_model_data)
    return jsonify(response_data.model_dump(exclude_none=True)), 200

def get_consultant_schedule_controller(consultant_id: int):
    """GET /consultants/{consultantId}/schedule - Belirli bir danışmanın uygunluk takvimini getirir."""
    availability_slots_sql = consultancy_service.get_consultant_availability(advisor_id=consultant_id)
    response_data_slots = []
    for slot_sql in availability_slots_sql:
        slot_status: AvailabilitySlotStatus = "booked" if slot_sql.is_booked else "available"
        pydantic_slot = AvailabilitySlotResponse(
            slot_id=slot_sql.slot_id,
            start_time=slot_sql.start_time,
            end_time=slot_sql.end_time,
            status=slot_status
        )
        response_data_slots.append(pydantic_slot.model_dump())
    return jsonify(response_data_slots), 200



def request_appointment_controller():
    """POST /appointments/request - Giriş yapmış kullanıcının randevu talep etmesini sağlar."""
    current_user = _get_current_user_info_from_token()
    if current_user["user_type"] != "user":
        raise AuthorizationError(message="Bu işlem için 'user' rolü gereklidir.")

    json_data = request.get_json()
    if not json_data:
        raise ValidationError(message="İstek gövdesi boş olamaz.", status_code=400)
    try:
        appointment_data_pydantic = CreateAppointmentRequest(**json_data)
    except PydanticValidationError as e_pydantic:
        raise ValidationError(message="İstek verisi doğrulama hatası.", details=e_pydantic.errors(), status_code=400)

    new_appointment_sql = consultancy_service.create_appointment(
        user_id=current_user["user_id"], 
        appointment_data=appointment_data_pydantic
    )
    
    apt_resp = AppointmentResponse.model_validate(new_appointment_sql)
  
    if new_appointment_sql.user:
        apt_resp.userFirstName = new_appointment_sql.user.firstName
        apt_resp.userLastName = new_appointment_sql.user.lastName
    if new_appointment_sql.advisor:
        apt_resp.consultantFirstName = new_appointment_sql.advisor.firstName
        apt_resp.consultantLastName = new_appointment_sql.advisor.lastName
            
    return jsonify(apt_resp.model_dump(exclude_none=True)), 201

def get_my_user_appointments_controller():
    """GET /users/me/appointments - Giriş yapmış kullanıcının tüm randevularını listeler."""
    current_user = _get_current_user_info_from_token()
    if current_user["user_type"] != "user":
        raise AuthorizationError(message="Bu işlem için 'user' rolü gereklidir.")

    status_filter = request.args.get('status')
    appointments_sql = consultancy_service.get_user_appointments(
        user_id=current_user["user_id"], 
        status_filter=status_filter
    )
    response_data_list = []
    for apt_sql in appointments_sql:
        apt_resp = AppointmentResponse.model_validate(apt_sql)

        if apt_sql.user: 
            apt_resp.userFirstName = apt_sql.user.firstName
            apt_resp.userLastName = apt_sql.user.lastName
        if apt_sql.advisor:
            apt_resp.consultantFirstName = apt_sql.advisor.firstName
            apt_resp.consultantLastName = apt_sql.advisor.lastName
        response_data_list.append(apt_resp.model_dump(exclude_none=True))
    return jsonify(response_data_list), 200
    
def get_my_user_appointment_details_controller(appointment_id: int):
    """GET /users/me/appointments/{appointmentId} - Giriş yapmış kullanıcının belirli bir randevusunun detaylarını getirir."""
    current_user = _get_current_user_info_from_token()
    if current_user["user_type"] != "user":
        raise AuthorizationError(message="Bu işlem için 'user' rolü gereklidir.")

    appointment_sql = consultancy_service.get_user_appointment_details(
        user_id=current_user["user_id"], 
        appointment_id=appointment_id
    )
    apt_resp = AppointmentResponse.model_validate(appointment_sql)
    if appointment_sql.user:
        apt_resp.userFirstName = appointment_sql.user.firstName
        apt_resp.userLastName = appointment_sql.user.lastName
    if appointment_sql.advisor:
        apt_resp.consultantFirstName = appointment_sql.advisor.firstName
        apt_resp.consultantLastName = appointment_sql.advisor.lastName
    return jsonify(apt_resp.model_dump(exclude_none=True)), 200


def rate_appointment_controller(appointment_id: int):
    """POST /appointments/{appointmentId}/rate - Kullanıcının tamamlanmış bir randevuyu puanlamasını sağlar."""
    current_user = _get_current_user_info_from_token()
    if current_user["user_type"] != "user":
        raise AuthorizationError(message="Bu işlem için 'user' rolü gereklidir.")

    json_data = request.get_json()
    if not json_data:
        raise ApiBaseError(message="İstek gövdesi boş olamaz.", status_code=400, error_code="BAD_REQUEST")
    try:
        rating_data_pydantic = RateAppointmentRequest(**json_data)
    except PydanticValidationError as e_pydantic:
        raise ValidationError(message="Puanlama verisi doğrulama hatası.", details=e_pydantic.errors(), status_code=400)

    new_feedback_sql = consultancy_service.submit_appointment_rating(
        user_id=current_user["user_id"],
        appointment_id=appointment_id,
        rating_data=rating_data_pydantic
    )
    
    fb_resp = FeedbackResponse.model_validate(new_feedback_sql)
    if new_feedback_sql.user: 
         fb_resp.userFirstName = new_feedback_sql.user.firstName
        
    return jsonify(fb_resp.model_dump(exclude_none=True)), 201



def get_my_advisor_appointments_controller(): 
    """GET /advisor/me/appointments - Giriş yapmış danışmanın tüm randevularını listeler."""
    current_user = _get_current_user_info_from_token() 
    if current_user["user_type"] != "advisor":
        raise AuthorizationError(message="Bu işlem için 'advisor' rolü gereklidir.")

    status_filter = request.args.get('status')
    appointments_sql = consultancy_service.get_advisor_appointments(
        advisor_id=current_user["user_id"], 
        status_filter=status_filter
    )
    response_data_list = []
    for apt_sql in appointments_sql:
        apt_resp = AppointmentResponse.model_validate(apt_sql)
        if apt_sql.user:
            apt_resp.userFirstName = apt_sql.user.firstName
            apt_resp.userLastName = apt_sql.user.lastName
        if apt_sql.advisor: 
            apt_resp.consultantFirstName = apt_sql.advisor.firstName
            apt_resp.consultantLastName = apt_sql.advisor.lastName
        response_data_list.append(apt_resp.model_dump(exclude_none=True))
    return jsonify(response_data_list), 200

def update_my_advisor_appointment_controller(appointment_id: int):
    """PATCH /advisor/me/appointments/{appointmentId} - Danışmanın bir randevunun durumunu veya detaylarını güncellemesi."""
    current_user = _get_current_user_info_from_token() 
    if current_user["user_type"] != "advisor":
        raise AuthorizationError(message="Bu işlem için 'advisor' rolü gereklidir.")
    
    json_data = request.get_json()
    if not json_data : 
        raise ApiBaseError(message="Güncellenecek veri bulunmuyor.", status_code=400, error_code="BAD_REQUEST")
    try:
        update_data_pydantic = UpdateAppointmentRequestAdvisor(**json_data)
    except PydanticValidationError as e_pydantic:
        raise ValidationError(message="Güncelleme verisi doğrulama hatası.", details=e_pydantic.errors(), status_code=400)

    updated_appointment_sql = consultancy_service.update_advisor_appointment(
        advisor_id=current_user["user_id"],
        appointment_id=appointment_id,
        update_data=update_data_pydantic
    )
    apt_resp = AppointmentResponse.model_validate(updated_appointment_sql)
    if updated_appointment_sql.user:
        apt_resp.userFirstName = updated_appointment_sql.user.firstName
        apt_resp.userLastName = updated_appointment_sql.user.lastName
    if updated_appointment_sql.advisor:
        apt_resp.consultantFirstName = updated_appointment_sql.advisor.firstName
        apt_resp.consultantLastName = updated_appointment_sql.advisor.lastName
    return jsonify(apt_resp.model_dump(exclude_none=True)), 200

def update_my_advisor_schedule_controller():
    """PUT /advisor/me/schedule - Danışmanın kendi uygunluk takvimini güncellemesi."""
    current_user = _get_current_user_info_from_token() 
    if current_user["user_type"] != "advisor":
        raise AuthorizationError(message="Bu işlem için 'advisor' rolü gereklidir.")

    json_data = request.get_json()
    if not json_data:
        raise ApiBaseError(message="İstek gövdesi boş olamaz.", status_code=400, error_code="BAD_REQUEST")
    try:
        schedule_data_pydantic = UpdateConsultantScheduleRequest(**json_data)
    except PydanticValidationError as e_pydantic:
        raise ValidationError(message="Takvim verisi doğrulama hatası.", details=e_pydantic.errors(), status_code=400)
    
    updated_slots_sql = consultancy_service.update_advisor_schedule(
        advisor_id=current_user["user_id"],
        schedule_data=schedule_data_pydantic
    )
    
    response_data_slots = []
    for slot_sql in updated_slots_sql:
        slot_status: AvailabilitySlotStatus = "booked" if slot_sql.is_booked else "available" 
        pydantic_slot = AvailabilitySlotResponse(
            slot_id=slot_sql.slot_id,
            start_time=slot_sql.start_time,
            end_time=slot_sql.end_time,
            status=slot_status
        )
        response_data_slots.append(pydantic_slot.model_dump())
        
    return jsonify(response_data_slots), 200

def get_my_advisor_feedback_controller():
    """GET /advisor/me/feedback - Giriş yapmış danışmanın aldığı tüm geri bildirimleri listeler."""
    current_user = _get_current_user_info_from_token() 
    if current_user["user_type"] != "advisor":
        raise AuthorizationError(message="Bu işlem için 'advisor' rolü gereklidir.")

    feedbacks_sql = consultancy_service.get_advisor_feedback(advisor_id=current_user["user_id"])
    response_data_list = []
    for fb_sql in feedbacks_sql:
        fb_resp = FeedbackResponse.model_validate(fb_sql)
        if fb_sql.user: 
            fb_resp.userFirstName = fb_sql.user.firstName
        response_data_list.append(fb_resp.model_dump(exclude_none=True))
    return jsonify(response_data_list), 200