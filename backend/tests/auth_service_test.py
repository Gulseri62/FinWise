import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import Keys
from service import auth_service

vrt = {
    "firstName": "Sumeyye",
    "lastName": "Eliacik",
    "email": "sumeyyeeliacik2@gmail.com",
    "password": "abc123"
}

result = auth_service.AuthService().create_user(vrt)
print(result)

login={
    "email": "sumeyyeeliacik2@gmail.com",
    "password": "abc123"
}
sonuc =auth_service.AuthService().authenticate_user(login)
print(sonuc)
auth_service=auth_service.AuthService()
reset_link_response = auth_service.send_reset_link("sumeyyeeliacik2@gmail.com")
print(reset_link_response)

# Şifreyi sıfırlama
reset_data = {
    "resetToken": reset_link_response["resetToken"],
    "newPassword": "newPassword123"
}
reset_response = auth_service.reset_user_password(reset_data)
print(reset_response)
print("Private Key İçeriği (Test Dosyasından):")
print(Keys.pem_private())