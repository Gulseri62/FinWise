import os
import logging
from flask import Flask
from flask_cors import CORS
from logging.handlers import RotatingFileHandler

from router.routes import auth_bp
from exceptions.auth_error_handler import register_error_handlers
from database.mysql_connector import db
from config.config import Config 

def configure_logging(app: Flask):
    log_level = logging.DEBUG if app.debug else logging.INFO
    log_file_path = 'logs/app.log'
    
    
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )


    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    app.logger.addHandler(console_handler)


    file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(log_level)
    app.logger.info("Loglama altyapısı hazır.")

def create_app():
    app = Flask(__name__)
    CORS(app)

   
    app.config.from_object(Config)

  
    db.init_app(app)
    configure_logging(app)
    register_error_handlers(app)


    app.register_blueprint(auth_bp)
    app.logger.info("Auth Blueprint ve Hata Yönetimi kaydedildi.")

    with app.app_context():

        db.create_all()
        app.logger.info("Veritabanı tabloları kontrol edildi.")

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))

    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))