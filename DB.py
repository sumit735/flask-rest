from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv() 

db = SQLAlchemy()
jwt_secret = os.environ.get("JWT_SECRET_KEY")
SMS_GATEWAY_UID = os.environ.get("SMS_GATEWAY_UID")
SMS_GATEWAY_PASS = os.environ.get("SMS_GATEWAY_PASS")
SG_SENDER_ID = os.environ.get("SG_SENDER_ID")