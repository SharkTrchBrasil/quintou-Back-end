import firebase_admin
from firebase_admin import credentials, messaging
import os
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Firebase App
_firebase_initialized = False

def init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return
        
    cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", None)
    if not cred_path or not os.path.exists(cred_path):
        logger.warning(f"Firebase credentials not found at {cred_path}. Push notifications will be disabled.")
        return
        
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")

# Try to initialize at module import, but it's safe if it fails (will just warn)
init_firebase()

class FirebaseService:
    @staticmethod
    def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None) -> bool:
        if not _firebase_initialized:
            logger.warning("Attempted to send push notification, but Firebase is not initialized.")
            return False
            
        if not fcm_token:
            return False
            
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=fcm_token,
            )
            response = messaging.send(message)
            logger.info(f"Successfully sent message: {response}")
            return True
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
