from flask import request, jsonify
import jwt
from config.config import Keys
from exceptions.auth_error_handler import AuthorizationError, TokenError, ApiBaseError

def _get_current_user_info_from_token():
    """
    Rapor 5.1: Token üzerinden kullanıcı kimliğini doğrular.
    Bu fonksiyon tüm modüllerde (Bütçe, Öneri vb.) ortak kullanılacak.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise AuthorizationError(message="Yetkilendirme başlığı eksik veya geçersiz.")
    
    token = auth_header.split(" ")[1]
    try:
      
        decoded_payload = jwt.decode(
            token, 
            Keys.pem_public(), 
            algorithms=["RS256"],
            options={"require": ["exp", "sub", "email", "user_type"]}
        )
        user_id = int(decoded_payload.get("sub"))
        if not user_id:
            raise TokenError(message="Token içeriği kullanıcı kimliği için eksik.")
        return {"user_id": user_id, "user_type": decoded_payload.get("user_type")}
    except jwt.ExpiredSignatureError:
        raise TokenError(message="Token süresi dolmuş.")
    except jwt.InvalidTokenError:
        raise TokenError(message="Geçersiz token.")
    except Exception as e:
        raise AuthorizationError(message=f"Token doğrulama sorunu: {str(e)}")



def signup():
    return jsonify({"message": "Signup logic will be here"}), 201

def signin():
    return jsonify({"message": "Signin logic will be here"}), 200

def get_my_profile():
    user_info = _get_current_user_info_from_token()
    return jsonify(user_info), 200