import firebase_admin
from firebase_admin import credentials, firestore
from .config import FIREBASE_CREDENTIALS_TYPE, PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL, TOKEN_URI

#Initialize Firebase
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": PROJECT_ID,
    "private_key": FIREBASE_PRIVATE_KEY,
    "client_email": FIREBASE_CLIENT_EMAIL,
    "token_uri": TOKEN_URI
})
firebase_admin.initialize_app(cred)

db = firestore.client()