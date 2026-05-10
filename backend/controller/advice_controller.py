from flask import request, jsonify
from pydantic import ValidationError as PydanticValidationError

from service.advice_service import AdviceService
from models.advice_models import (
    PersonalizedAdviceResponse,
    AdviceFeedbackRequest,    
    AdviceFeedbackResponse    
)

from exceptions.auth_error_handler import ApiBaseError, ValidationError as CustomValidationError

import jwt
from config.config import Keys # JWT keylerini almak için
from exceptions.auth_error_handler import AuthorizationError, TokenError






def _get_current_user_info_from_token(): #budget modülünde de olduğu gibi user doğrulama işlemini yapalım
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise AuthorizationError(message="Yetkilendirme başlığı eksik veya geçersiz.")
    token = auth_header.split(" ")[1]
    try:
        decoded_payload = jwt.decode(token, Keys.pem_public(), algorithms=["RS256"],
                                     options={"require": ["exp", "sub", "email", "user_type"]})
        user_id = int(decoded_payload.get("sub"))
        if not user_id:
            raise TokenError(message="Token içeriği kullanıcı kimliği için eksik.")
        return {"user_id": user_id, "user_type": decoded_payload.get("user_type")}
    except jwt.ExpiredSignatureError:
        raise TokenError(message="Token süresi dolmuş.")
    except jwt.InvalidTokenError:
        raise TokenError(message="Geçersiz token.")
    except TokenError:
        raise
    except Exception as e:
        raise AuthorizationError(message=f"Token doğrulama sırasında bir sorun oluştu: {str(e)}")




advice_service = AdviceService()



def get_personalized_advice(): #GET /advice/personal
    """
    Kullanıcı için kişiselleştirilmiş ve aktif finansal önerileri getirir.
    """
    try:
        current_user = _get_current_user_info_from_token()
        user_id = current_user["user_id"]

        active_advices_db = advice_service.get_personalized_advice(user_id=user_id) 

        # SQLAlchemy nesnelerini Pydantic modeline dönüştür
        response_data_list = [PersonalizedAdviceResponse.model_validate(advice) for advice in active_advices_db]

        return jsonify([advice.model_dump() for advice in response_data_list]), 200

    except Exception as e:
        if isinstance(e, ApiBaseError):
            raise 
        else: 
            raise ApiBaseError(message=f"Öneriler alınırken sunucuda beklenmedik bir sorun oluştu: {str(e)}", status_code=500)


def submit_advice_feedback(): # POST /advice/feedback
    """
    Bir finansal öneriye kullanıcı geri bildirimi gönderir.
    """
    try:
        current_user = _get_current_user_info_from_token()
        user_id = current_user["user_id"]

        json_data = request.get_json() #gelen veriyi al
        if not json_data:
            raise CustomValidationError(message="İstek gövdesi boş olamaz.", status_code=400)

       
        validated_feedback_data = AdviceFeedbackRequest(**json_data) #pydanticle doğrula

        # Servis katmanını çağır
        saved_feedback_db = advice_service.record_feedback(
            user_id=user_id,
            feedback_data=validated_feedback_data
        )

        # Başarılı yanıtı Pydantic modeli ile oluştur ve döndür
        response_data = AdviceFeedbackResponse.model_validate(saved_feedback_db)
        return jsonify(response_data.model_dump()), 201 

    except PydanticValidationError as e:
        raise CustomValidationError(message="Geri bildirim verileri geçersiz.", details=e.errors(), status_code=400)
    



