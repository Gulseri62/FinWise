from flask import Blueprint
# Sadece Auth controller'ı dahil ediyoruz
from controller.auth_controller import signup, signin, reset_password, refresh, forgot_password, get_my_profile

"""Authentication modülünün endpointleri ve routeları"""
auth_bp = Blueprint('auth', __name__, url_prefix='/auth') 

auth_bp.add_url_rule('/signup', methods=['POST'], view_func=signup)
auth_bp.add_url_rule('/signin', methods=['POST'], view_func=signin)
auth_bp.add_url_rule('/forgot-password', methods=['POST'], view_func=forgot_password)
auth_bp.add_url_rule('/refresh', methods=['POST'], view_func=refresh)
auth_bp.add_url_rule('/reset-password', methods=['POST'], view_func=reset_password)
auth_bp.add_url_rule('/me', methods=['GET'], view_func=get_my_profile)