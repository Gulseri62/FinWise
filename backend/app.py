import os
from flask import Flask, jsonify
from flask_cors import CORS
from config.config import Config
from database.mysql_connector import db
from router.routes import auth_bp



def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(auth_bp)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-key-123')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    CORS(app)
    db.init_app(app)

    @app.route('/')
    def health_check():
        return jsonify({
            "status": "success",
            "message": "Finance Project API is running",
            "version": "1.0.0"
        }), 200

    
    with app.app_context():
     ########################################################
        db.create_all() 

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)