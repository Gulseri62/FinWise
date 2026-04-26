from flask import jsonify, current_app, request
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError 
from database.mysql_connector import db 





class ApiBaseError(Exception):
   
    status_code: int = 500
    error_code: str = "SERVER_ERROR"
    message: str = "Sunucu kaynaklı bir hata oluştu."
    details: dict[str, any] = None  

    def __init__(
        self,
        message=None,
        status_code=None,
        error_code=None,
        details=None
    ):
        effective_message = message if message is not None else self.message
        super().__init__(effective_message)

        self.message = effective_message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        if details is not None:
            self.details = details

    def to_dict(self):
        response_body = {
            'errorCode': self.error_code,
            'errorMessage': self.message,
        }
        if self.details is not None:
            response_body['details'] = self.details
        return response_body

    def to_response(self):
   
        response = jsonify(self.to_dict())
        response.status_code = self.status_code
        return response


class ValidationError(ApiBaseError): 
    status_code = 400
    error_code = "VALIDATION_ERROR"
    message = "Geçersiz istek. Eksik veya hatalı alanlar."


class AuthenticationError(ApiBaseError):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    message = "Kimlik doğrulama başarısız."
    details = "E-posta veya şifre hatalı."

class AuthorizationError(ApiBaseError):
    status_code = 403
    error_code = "AUTHORIZATION_FAILED"
    message = "Bu işlem için yetkiniz bulunmamaktadır."

class NotFoundError(ApiBaseError): 
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND" 
    message = "İstenen kaynak bulunamadı."

class ConflictError(ApiBaseError):
    status_code = 409
    error_code = "CONFLICT_ERROR"
    message = "İşlem sırasında bir çakışma oluştu."

class TokenError(ApiBaseError):
    status_code = 401 
    error_code = "TOKEN_INVALID"
    message = "Token geçersiz veya süresi dolmuş."

class RateLimitExceededError(ApiBaseError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Çok fazla deneme yaptınız."


class EducationNotFoundError(NotFoundError): 
    error_code = "EDUCATION_NOT_FOUND"
    message = "Belirtilen eğitim bulunamadı."

class ApplicationNotFoundError(NotFoundError): 
    error_code = "APPLICATION_NOT_FOUND"
    message = "Belirtilen başvuru bulunamadı."

class DuplicateApplicationError(ConflictError): 
    error_code = "DUPLICATE_APPLICATION"
    message = "Bu e-posta adresi ile bu eğitime daha önce başvuru yapılmış."

class QuotaFullError(ConflictError): 
    error_code = "QUOTA_FULL_ERROR"
    message = "Eğitim kontenjanı dolu olduğu için işlem gerçekleştirilemedi."
    status_code = 409 

class InvalidApplicationStatusError(ApiBaseError): 
    status_code = 400 
    error_code = "INVALID_APPLICATION_STATUS"
    message = "Başvuru durumu bu işlem için uygun değil."



def register_error_handlers(app):
   

    @app.errorhandler(ApiBaseError) 
    def handle_api_error(error: ApiBaseError):
        current_app.logger.error(
            f"API Hatası: {error.error_code} ({error.status_code}) - {error.message} "
            f"- Details: {error.details} - URL: {request.path} - Metod: {request.method}"
        )
        return error.to_response()

    @app.errorhandler(404) 
    def handle_flask_not_found(error): 
        api_error = NotFoundError(
            error_code="ENDPOINT_NOT_FOUND",
            message="İstenen API endpoint'i bulunamadı.",
            details={"path": request.path}
        )
        current_app.logger.warning(f"404 Endpoint Bulunamadı - URL: {request.path}")
        return api_error.to_response()

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        api_error = ApiBaseError(
            status_code=405,
            error_code="METHOD_NOT_ALLOWED",
            message="Bu URL için izin verilmeyen HTTP metodu.",
            details={"method": request.method, "allowed_methods": getattr(error, 'valid_methods', []) }
        )
        current_app.logger.warning(f"405 Metod İzin Verilmedi - Metod: {request.method}, URL: {request.path}")
        return api_error.to_response()



    @app.errorhandler(PydanticValidationError)
    def handle_pydantic_validation_error(error: PydanticValidationError):
        error_details = {}
        for err in error.errors():
            field_parts = []
            for loc_item in err.get('loc', ['unknown']):
                field_parts.append(str(loc_item))
            field = ".".join(field_parts)
            message = err.get('msg', 'Bilinmeyen validasyon hatası')
            error_details[field] = message
            api_error = ValidationError( 
                details={
                    "validationErrors": error_details,
                    "receivedData": request.get_json(silent=True) 
                }
            )
            current_app.logger.warning(
                f"Pydantic Validasyon Hatası: {error_details} - URL: {request.path} - Metod: {request.method}"
            )
            return api_error.to_response()
    

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error: IntegrityError):
        db.session.rollback() 
        original_error_msg = str(getattr(error.orig, 'msg', str(error.orig))) 
        current_app.logger.error(
            f"Veritabanı Bütünlük Hatası: {original_error_msg} - URL: {request.path} - Metod: {request.method}"
        )
        api_error = ConflictError(
            message="Girilen veri mevcut bir kayıtla çakışıyor olabilir.",
            details={"db_error": original_error_msg}
        )
        return api_error.to_response()


    @app.errorhandler(Exception) 
    def handle_generic_exception(error: Exception):
        import traceback
        tb_str = traceback.format_exc()
        current_app.logger.error(
            f"Beklenmedik Sunucu Hatası ({type(error).__name__}): {error}\n{tb_str}"
        )
        api_error = ApiBaseError( 
            message="Sunucuda beklenmedik bir hata oluştu. Lütfen daha sonra tekrar deneyin.", 
            details={"exception_type": type(error).__name__, "trace": tb_str if current_app.debug else "Traceback gizlendi."}
        )
        return api_error.to_response()
