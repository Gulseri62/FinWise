from flask import request, jsonify
from pydantic import ValidationError as PydanticValidationError

from service.budget_service import BudgetService
from models.budget_models import (
    BudgetEntryCreateRequest,
    BudgetEntryResponse,
    TransactionQuerySchema,
    PaginatedBudgetEntryResponse,
    BudgetReportRequestSchema,
    BudgetReportResponse
)

from exceptions.auth_error_handler import ApiBaseError, ValidationError as CustomValidationError 
import jwt
from config.config import Keys 
from exceptions.auth_error_handler import AuthorizationError, TokenError

def _get_current_user_info_from_token():
    """Yetkilendirme işlemleri için kullanıcının jwt bilgilerine eriş."""


    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise AuthorizationError(message="Yetkilendirme başlığı eksik veya geçersiz.")

    token = auth_header.split(" ")[1]
    try:
        decoded_payload = jwt.decode(token, Keys.pem_public(), algorithms=["RS256"],
                                     options={"require": ["exp", "sub", "email", "user_type"]})

        user_id = int(decoded_payload.get("sub"))
        user_type = decoded_payload.get("user_type") 

        if not user_id: 
            raise TokenError(message="Token içeriği kullanıcı kimliği için eksik.")

        return {"user_id": user_id, "user_type": user_type}
    except jwt.ExpiredSignatureError:
        raise TokenError(message="Token süresi dolmuş.")
    except jwt.InvalidTokenError:
        raise TokenError(message="Geçersiz token.")
    except TokenError: 
        raise
    except Exception as e: 
        # 
        raise AuthorizationError(message=f"Token doğrulama sırasında bir sorun oluştu: {str(e)}")



budget_service = BudgetService()


def add_income_entry(): #POST /budget/income
    """
    Gelir girişi ekler.
    """
    try:
        current_user = _get_current_user_info_from_token() #kullanıcıya eriş
        user_id = current_user["user_id"]

        
        json_data = request.get_json() #istekten json verilerini al
        if not json_data:
            raise CustomValidationError(message="İstek gövdesi boş olamaz.", status_code=400)

        validated_data = BudgetEntryCreateRequest(**json_data) #pydantic ile doğrula

        new_income_entry_db = budget_service.add_budget_entry(
            user_id=user_id,
            entry_data=validated_data,
            entry_type='income' # Bu endpoint gelir ekleme için 
        )

        response_data = BudgetEntryResponse.model_validate(new_income_entry_db)# yanıt başarıloysa pydantic modeliyle oluştur
        return jsonify(response_data.model_dump()), 201 

    except PydanticValidationError as e: 
        raise CustomValidationError(message="Girdi verileri geçersiz.", details=e.errors(), status_code=400)
    


def add_expense_entry():#POST /budget/expense 
    """Gider girişi ekler. """
    try:
        current_user = _get_current_user_info_from_token() #kullanıcıya eriş
        user_id = current_user["user_id"]

        
        json_data = request.get_json() #istekten json verilerini al
        if not json_data:
            raise CustomValidationError(message="İstek gövdesi boş olamaz.", status_code=400)

        validated_data = BudgetEntryCreateRequest(**json_data) #pydantic ile doğrula

        new_income_entry_db = budget_service.add_budget_entry(
            user_id=user_id,
            entry_data=validated_data,
            entry_type='expense' # Bu endpoint gelir ekleme için 
        )

        response_data = BudgetEntryResponse.model_validate(new_income_entry_db)# yanıt başarıloysa pydantic modeliyle oluştur
        return jsonify(response_data.model_dump()), 201 

    except PydanticValidationError as e: 
        raise CustomValidationError(message="Girdi verileri geçersiz.", details=e.errors(), status_code=400)
    

def get_transactions():#GET /budget/transactions
    """İşlem geçmişini listeler. """

    try:
        current_user = _get_current_user_info_from_token()
        user_id = current_user["user_id"]

        query_params_dict = {}  #paarmetreleri alalım
        if 'start_date' in request.args:
            query_params_dict['start_date'] = request.args.get('start_date')
        if 'end_date' in request.args:
            query_params_dict['end_date'] = request.args.get('end_date')
        if 'category' in request.args:
            query_params_dict['category'] = request.args.get('category')
        if 'entry_type' in request.args:
            query_params_dict['entry_type'] = request.args.get('entry_type')
        if 'page' in request.args:
            query_params_dict['page'] = request.args.get('page')
        if 'per_page' in request.args:
            query_params_dict['per_page'] = request.args.get('per_page')
        
        validated_query_params = TransactionQuerySchema(**query_params_dict) #pydanticle doğrula

        paginated_response_data = budget_service.get_transactions(user_id=user_id,query_params=validated_query_params)

        return jsonify(paginated_response_data.model_dump()), 200 #yanıtı jsonify yap ve gönder

    except PydanticValidationError as e:
        
        raise CustomValidationError(message="Geçersiz filtre veya sayfalama parametreleri.", details=e.errors(), status_code=400)
    
    

def delete_budget_entry(transaction_id: int):#DELETE /budget/transactions/{transactionId}
        current_user = _get_current_user_info_from_token()
        user_id = current_user["user_id"]
        deleted=budget_service.delete_budget_entry(user_id=user_id,entry_id=transaction_id)
        if deleted:
            return jsonify({}), 204
        else:
            raise ApiBaseError(message="Kayıt silinemedi, bilinmeyen bir sorun oluştu.", status_code=500)


def get_budget_report(): #GET /budget/report
    try:
        current_user = _get_current_user_info_from_token()
        user_id = current_user["user_id"]

        query_report_type = request.args.get('report_type') 
        if query_report_type:
            validated_report_params = BudgetReportRequestSchema(report_type=query_report_type)
        else:
            validated_report_params = BudgetReportRequestSchema()

        report_data_pydantic = budget_service.generate_financial_report(user_id=user_id,report_params=validated_report_params )

        
        return jsonify(report_data_pydantic.model_dump()), 200

    except PydanticValidationError as e:
        raise CustomValidationError(message="Geçersiz rapor tipi parametresi.", details=e.errors(), status_code=400)
    
        

    