import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
   
    BASE_DIR = Path(__file__).parent.parent
    KEY_DIR = Path(__file__).parent / "keys"

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

   
    JWT_ALGORITHM = "RS256" 

  
    EDUCATION_QUOTA = int(os.getenv("EDUCATION_QUOTA", 10))
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

class Keys:
    
    KEY_DIR = Path(__file__).parent / "keys"

    @classmethod
    def pem_private(cls):
        with open(cls.KEY_DIR / "private_key.pem", "rb") as f: 
            return f.read().decode('utf-8')  

    @classmethod
    def pem_public(cls):
        with open(cls.KEY_DIR / "public_key.pem", "rb") as f:  
            return f.read().decode('utf-8')

  
    DEFAULT_ADVISORS_INFOS = [
        # 
    ]