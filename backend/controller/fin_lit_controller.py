from flask import jsonify,request,current_app
from models.fin_lit_models import (
    ApplicationRequest,
    ApplicationResponse,
    HomePageInfo,
    CourseContentPackage,
    ApplicationForm,
    EducationResponse, 
)
from pydantic import ValidationError as PydanticBuiltinValidationError # Pydantic'in kendi ValidationError'u
from service.fin_lit_service import FinancialLiteracyService





fin_lit_service = FinancialLiteracyService() #service sınıfının instance i




def get_general_fin_lit_info():

    data_dict = fin_lit_service.get_fin_lit_home_page_content()
    response_model = HomePageInfo(**data_dict)
    return jsonify(response_model.model_dump()), 200 



def get_course_package():
    
    data_dict= fin_lit_service.get_course_package_details()
    course_data_for_pydantic = {
            "paketAdi": data_dict.get("paketAdi"), 
            "paketAciklamasi": data_dict.get("paketAciklamasi"), 
            "moduller": data_dict.get("moduller", []) 
        }
    response_model = CourseContentPackage(**course_data_for_pydantic)
    return jsonify(response_model.model_dump()), 200

def get_application_form_info():
    data_dict = fin_lit_service.get_application_form_data()
    response_model = ApplicationForm(**data_dict)
    return jsonify(response_model.model_dump()), 200


def submit_application():
    data = request.get_json() #gelen json verisini al
    application_input = ApplicationRequest(**data)  #pydantic ile veri doğrulama
    result_dict = fin_lit_service.create_education_application(application_input.model_dump()) # doğrulaanna pydantic verisini srvice e gönder.
    response_model = ApplicationResponse(**result_dict)
    return jsonify(response_model.model_dump()), 201 #olumlu yanıt modeldump ile yanıt oluşturalım. servisten olumlu yanıt gelir

