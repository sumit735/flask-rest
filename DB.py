from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv() 

db = SQLAlchemy()
jwt_secret = os.environ.get("JWT_SECRET_KEY")