from flask import Blueprint, jsonify

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def sign_up():
    # Rapor 5.1: sign_up(data) rutini
    return jsonify({"message": "Sign up endpoint ready"}), 201

@auth_bp.route('/login', methods=['POST'])
def sign_in():
    # Rapor 5.1: sign_in() rutini
    return jsonify({"message": "Sign in endpoint ready"}), 200