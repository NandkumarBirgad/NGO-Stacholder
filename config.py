import pymysql
import firebase_admin
from firebase_admin import credentials, auth, firestore

class Config:
    # MySQL settings
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'sagar123'
    MYSQL_DB = 'ngo_management_system'
    MYSQL_CURSORCLASS = 'DictCursor'

# --------- MySQL Connection Function ----------
def get_mysql_connection():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

# --------- Firebase Admin SDK Initialization ----------
cred = credentials.Certificate("serviceAccountKey.json.json")
firebase_admin.initialize_app(cred)

# Firestore DB (For storing user roles)
firestore_db = firestore.client()
